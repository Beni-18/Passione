"""Orchestrates the full training run (plan §1, §9, §11, §13).

load -> adapt -> label -> features -> split -> fit -> evaluate -> gate ->
write versioned artifacts -> (maybe) promote `latest.json`.

This module owns honest row-counting (`rows_received/processed/failed`) and
the `progress_cb` calls that make the backend's GET /status real instead of
hardcoded (handout requirement #5). Never overwrites an existing version
directory (handout §2.7, §5).
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.model_selection import train_test_split

from mlcore import config
from mlcore.adapters import compute_label, movie_to_canonical
from mlcore.evaluate import evaluate
from mlcore.features import build_features
from mlcore.pipeline import make_pipeline

_ALGO_PREFIX = {"dummy": "dummy", "logreg": "lr", "random_forest": "rf"}


def _noop_cb(processed: int, failed: int, total: int, stage: str) -> None:
    return None


def _sha256_of_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_of_ids(ids) -> str:
    joined = ",".join(str(i) for i in sorted(int(i) for i in ids))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _next_version_dir(prefix: str) -> tuple[str, Path]:
    config.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    n = 1
    while True:
        version = f"{prefix}_v{n}"
        path = config.ARTIFACTS_DIR / version
        if not path.exists():
            return version, path
        n += 1


def _atomic_write_json(path: Path, obj: dict) -> None:
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(obj, f, indent=2, sort_keys=True, default=str)
        os.replace(tmp_path, path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def _known_categories(fitted_pipeline) -> dict:
    encoder = fitted_pipeline.named_steps["preprocess"].named_transformers_["cat"]
    return {
        col: sorted(str(c) for c in cats)
        for col, cats in zip(config.CATEGORICAL_FEATURES, encoder.categories_)
    }


def _feature_metadata(fitted_pipeline) -> dict:
    feature_specs = {
        "primary_genre": ("genres", "first element, else 'unknown'", "categorical"),
        "language": ("original_language", "passthrough, lowercased, else 'unknown'", "categorical"),
        "release_month": ("release_date", "month, zero-padded, else 'unknown'", "categorical"),
        "release_dayofweek": ("release_date", "day name, else 'unknown'", "categorical"),
        "duration_minutes": ("runtime", "passthrough (real, modeled)", "numeric"),
        "release_year": ("release_date", "year", "numeric"),
        "tag_count": ("keywords", "count", "numeric"),
        "title_length": ("title", "len()", "numeric"),
        "title_word_count": ("title", "whitespace token count", "numeric"),
        "title_caps_ratio": ("title", "uppercase letters / letters", "numeric"),
        "duration_missing": ("runtime", "isna()", "bool"),
        "is_holiday_season": ("release_date", "month in {11,12}", "bool"),
        "is_friday_release": ("release_date", "dayofweek == 4", "bool"),
        "has_tags": ("keywords", "count > 0", "bool"),
        "title_has_punctuation_hook": ("title", "'!' or '?' present", "bool"),
        "title_has_number": ("title", "contains a digit", "bool"),
        "duration_minutes_indicator": ("runtime", "SimpleImputer missing-indicator", "numeric"),
    }
    ordered = [
        {
            "name": name,
            "display_name": config.DISPLAY_NAMES.get(name, name),
            "source_field": feature_specs.get(name, ("", "", ""))[0],
            "transform": feature_specs.get(name, ("", "", ""))[1],
            "dtype": feature_specs.get(name, ("", "", ""))[2],
            "status": "modeled",
        }
        for name in config.ALL_FEATURES
    ]
    return {
        "features": ordered,
        "known_categories": _known_categories(fitted_pipeline),
        "display_names": config.DISPLAY_NAMES,
        "contract_field_mapping": {
            "title": "title", "genre": "genre -> primary_genre (first listed genre only)",
            "duration_minutes": "runtime (real, modeled)", "upload_time": "release_date (reframed, see plan §5)",
            "language": "original_language", "tags": "keywords",
        },
        "excluded_tier2_columns": [
            "budget", "production_companies", "production_countries", "spoken_languages", "cast", "crew",
            "overview",
        ],
        "excluded_leakage_columns": ["vote_count", "revenue", "vote_average", "status"],
    }


def train(
    csv_path: str | None = None,
    progress_cb: Callable | None = None,
    seed: int = config.SEED,
    algo: str = "logreg",
) -> dict:
    cb = progress_cb or _noop_cb

    if algo not in _ALGO_PREFIX:
        # Must NOT raise — contract says raises ONLY on an unreadable/absent
        # csv_path (plan §13). An invalid algo is a caller/config error, not
        # a filesystem error, and gets the same graceful-failure shape as
        # every other non-raising failure path below.
        cb(0, 0, 0, "failed")
        return {
            "model_version": None, "rows_received": 0, "rows_processed": 0, "rows_failed": 0,
            "metrics": {}, "artifacts_dir": None, "passed_gate": False, "promoted": False,
            "status": "failed", "detail": f"Unknown algo {algo!r}; expected one of {sorted(_ALGO_PREFIX)}.",
        }

    resolved_path = Path(csv_path) if csv_path else config.DEFAULT_TRAIN_CSV

    # Raises ONLY here — an unreadable/absent csv_path (contract, plan §13).
    if not resolved_path.exists():
        raise FileNotFoundError(f"Training CSV not found: {resolved_path}")

    cb(0, 0, 0, "loading")
    try:
        raw_df = pd.read_csv(resolved_path)
    except pd.errors.EmptyDataError:
        # Path exists but the file is truly empty (0 bytes, no header at all).
        # This is a data problem, not a missing-file problem — must NOT raise
        # (contract: raises ONLY on an unreadable/absent csv_path).
        cb(0, 0, 0, "failed")
        return {
            "model_version": None, "rows_received": 0, "rows_processed": 0, "rows_failed": 0,
            "metrics": {}, "artifacts_dir": None, "passed_gate": False, "promoted": False,
            "status": "failed", "detail": "Training CSV is completely empty (no header, no rows).",
        }
    rows_received = len(raw_df)

    if rows_received == 0:
        cb(0, 0, 0, "failed")
        return {
            "model_version": None, "rows_received": 0, "rows_processed": 0, "rows_failed": 0,
            "metrics": {}, "artifacts_dir": None, "passed_gate": False, "promoted": False,
            "status": "failed", "detail": "Training CSV has a header row but zero data rows (or is empty).",
        }

    cb(0, 0, rows_received, "adapting")
    canonical_df, rows_processed, rows_failed = movie_to_canonical(raw_df)

    if rows_processed == 0:
        cb(0, rows_failed, rows_received, "failed")
        return {
            "model_version": None, "rows_received": rows_received, "rows_processed": 0,
            "rows_failed": rows_failed, "metrics": {}, "artifacts_dir": None, "passed_gate": False,
            "promoted": False, "status": "failed",
            "detail": f"All {rows_received} rows failed to parse into canonical form.",
        }

    cb(rows_processed, rows_failed, rows_received, "featurizing")
    canonical_df = canonical_df.sort_values("id", kind="mergesort").reset_index(drop=True)
    y, threshold = compute_label(canonical_df)
    X, feature_names = build_features(canonical_df)
    ids = canonical_df["id"]

    idx = np.arange(len(X))
    idx_train, idx_test = train_test_split(
        idx, test_size=config.TEST_SIZE, stratify=y, random_state=seed, shuffle=True
    )
    X_train, X_test = X.iloc[idx_train], X.iloc[idx_test]
    y_train, y_test = y.iloc[idx_train], y.iloc[idx_test]
    ids_train, ids_test = ids.iloc[idx_train], ids.iloc[idx_test]

    cb(rows_processed, rows_failed, rows_received, "training")
    fitted = make_pipeline(algo)
    fitted.fit(X_train, y_train)

    cb(rows_processed, rows_failed, rows_received, "evaluating")
    proba = fitted.predict_proba(X_test)[:, 1]
    eval_metrics = evaluate(y_test, proba)
    passed_gate = eval_metrics["roc_auc"] >= config.MIN_ROC_AUC

    cb(rows_processed, rows_failed, rows_received, "saving")
    prefix = _ALGO_PREFIX.get(algo, algo)
    model_version, version_dir = _next_version_dir(prefix)
    version_dir.mkdir(parents=True, exist_ok=False)  # never overwrite (plan §11)

    trained_at = datetime.now(timezone.utc).isoformat()
    metrics = {
        **eval_metrics,
        "model_version": model_version,
        "algo": algo,
        "trained_at": trained_at,
        "seed": seed,
        "label_strategy": "percentile_threshold",
        "threshold_percentile": config.POPULARITY_PERCENTILE,
        "popularity_threshold": threshold,
        "n_train": int(len(X_train)),
        "rows_received": rows_received,
        "rows_processed": rows_processed,
        "rows_failed": rows_failed,
        "passed_gate": passed_gate,
        "min_roc_auc_gate": config.MIN_ROC_AUC,
        "library_versions": {
            "scikit_learn": sklearn.__version__,
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "joblib": joblib.__version__,
        },
    }

    joblib.dump(fitted, version_dir / "model.joblib")
    joblib.dump(fitted.named_steps["preprocess"], version_dir / "encoder.joblib")
    _atomic_write_json(version_dir / "metrics.json", metrics)
    _atomic_write_json(version_dir / "feature_metadata.json", _feature_metadata(fitted))

    split_info = {
        "seed": seed,
        "test_size": config.TEST_SIZE,
        "n_train": int(len(idx_train)),
        "n_test": int(len(idx_test)),
        "train_ids_sha256": _sha256_of_ids(ids_train),
        "test_ids_sha256": _sha256_of_ids(ids_test),
        "source_file": str(resolved_path),
        "source_file_sha256": _sha256_of_file(resolved_path),
    }
    _atomic_write_json(version_dir / "split.json", split_info)

    # Promotion rule (plan §9, §11): only overwrite latest.json if the gate
    # passes AND this beats the incumbent by the promotion margin (or there
    # is no incumbent yet).
    promoted = False
    if passed_gate:
        incumbent_auc = None
        if config.LATEST_POINTER_PATH.exists():
            try:
                incumbent = json.loads(config.LATEST_POINTER_PATH.read_text())
                incumbent_auc = incumbent.get("roc_auc")
            except (json.JSONDecodeError, OSError):
                incumbent_auc = None
        if incumbent_auc is None or eval_metrics["roc_auc"] >= incumbent_auc + config.PROMOTION_MARGIN:
            _atomic_write_json(config.LATEST_POINTER_PATH, {
                "model_version": model_version,
                "path": str(version_dir),
                "promoted_at": trained_at,
                "roc_auc": eval_metrics["roc_auc"],
            })
            promoted = True

    cb(rows_processed, rows_failed, rows_received, "complete")
    return {
        "model_version": model_version,
        "rows_received": rows_received,
        "rows_processed": rows_processed,
        "rows_failed": rows_failed,
        "metrics": metrics,
        "artifacts_dir": str(version_dir),
        "passed_gate": passed_gate,
        "promoted": promoted,
        "status": "complete",
        "detail": f"Trained {model_version}: ROC-AUC={eval_metrics['roc_auc']:.4f}, "
                  f"gate={'passed' if passed_gate else 'FAILED'}, promoted={promoted}.",
    }
