"""Source-specific loaders (plan §2, §3, §4). One function per data source.

`movie_to_canonical()` is the only adapter needed for this hackathon: it turns
the raw Kaggle `movies_train.csv` into the canonical row shape (§1's "canonical
row is the contract boundary") — the SAME shape `schema.validate_metadata()`
produces from a live /predict body. Adding a second source later means writing
one more function here, never touching features.py, pipeline.py, or predict.py.

Never imported at inference time (see api.py / predict.py).
"""
from __future__ import annotations

import ast
import logging

import pandas as pd

from mlcore import config

logger = logging.getLogger(__name__)

# Columns actually read from the raw CSV. Anything else (vote_count, revenue,
# vote_average, status, budget, cast, crew, ...) is deliberately NOT loaded
# here — see plan §5 for the full leakage / Tier-2 rationale.
_RAW_COLUMNS = ["id", "title", "genres", "runtime", "release_date", "original_language", "keywords", "popularity"]


def _safe_literal_list(raw: object) -> tuple[list, bool]:
    """Parse a stringified Python list literal (e.g. "['Comedy', 'Foreign']").

    This dataset embeds Python repr syntax, NOT JSON (single quotes) — using
    json.loads here is the single most common silent-crash bug with this file
    (plan §3). Returns (list, ok); never raises.
    """
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return [], True
    if isinstance(raw, list):
        return raw, True
    if not isinstance(raw, str):
        return [], False
    try:
        parsed = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return [], False
    if not isinstance(parsed, list):
        return [], False
    return parsed, True


def movie_to_canonical(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
    """Convert raw movies_train.csv rows into the canonical /predict-shaped frame.

    Returns (canonical_df, rows_processed, rows_failed). A row is "failed" and
    dropped only when a field critical to labeling or modeling can't be
    recovered at all (missing id, missing/unparseable popularity, or an
    unparseable genres list with no title to fall back on). Everything else
    (missing runtime, missing release_date, empty keywords) is handled by the
    imputation path in preprocessing (plan §7), not dropped here.
    """
    missing = [c for c in _RAW_COLUMNS if c not in raw_df.columns]
    if missing:
        raise ValueError(f"movies_train.csv is missing expected columns: {missing}")

    df = raw_df[_RAW_COLUMNS].copy()
    rows_received = len(df)

    genres_parsed = df["genres"].apply(_safe_literal_list)
    df["_genres_list"] = genres_parsed.apply(lambda t: t[0])
    df["_genres_ok"] = genres_parsed.apply(lambda t: t[1])

    keywords_parsed = df["keywords"].apply(_safe_literal_list)
    df["_keywords_list"] = keywords_parsed.apply(lambda t: t[0])
    df["_keywords_ok"] = keywords_parsed.apply(lambda t: t[1])

    df["popularity"] = pd.to_numeric(df["popularity"], errors="coerce")
    df["_upload_time"] = pd.to_datetime(df["release_date"], format="%Y-%m-%d", errors="coerce")
    df["_duration"] = pd.to_numeric(df["runtime"], errors="coerce")
    df["_duration"] = df["_duration"].where(df["_duration"] >= 0)  # negative runtime -> null, not fabricated

    fail_mask = (
        df["id"].isna()
        | ~df["_genres_ok"]
        | ~df["_keywords_ok"]
        | df["popularity"].isna()
        | df["title"].isna()
        | (df["title"].astype(str).str.strip() == "")
    )
    rows_failed = int(fail_mask.sum())
    kept = df.loc[~fail_mask].copy()

    canonical = pd.DataFrame({
        "id": kept["id"].astype(int),
        "title": kept["title"].astype(str).str.strip(),
        "genre": kept["_genres_list"].apply(lambda g: str(g[0]).strip() if g else None),
        "duration_minutes": kept["_duration"],
        "upload_time": kept["_upload_time"],
        "language": kept["original_language"].apply(
            lambda v: str(v).strip().lower() if pd.notna(v) and str(v).strip() else None
        ),
        "tags": kept["_keywords_list"].apply(lambda kw: [str(t).strip() for t in kw if str(t).strip()]),
        "popularity": kept["popularity"],
    }).reset_index(drop=True)

    dup_ids = int(canonical["id"].duplicated().sum())
    if dup_ids:
        logger.warning("movie_to_canonical: %d duplicate ids found (expected 0)", dup_ids)

    rows_processed = len(canonical)
    return canonical, rows_processed, rows_failed


def compute_label(canonical_df: pd.DataFrame, percentile: float = config.POPULARITY_PERCENTILE) -> tuple[pd.Series, float]:
    """Freeze the popularity threshold (plan §4) and derive y.

    Computed ONCE on the full frame passed in (the caller — train.py — must
    pass the full training set here exactly once, before splitting, and reuse
    the returned threshold everywhere else; never recompute it).
    """
    threshold = float(canonical_df["popularity"].quantile(percentile))
    y = (canonical_df["popularity"] >= threshold).astype(int)
    return y, threshold


def load_training_frame(csv_path) -> dict:
    """Top-level entry point train.py calls. Loads, adapts, and labels in one shot."""
    raw_df = pd.read_csv(csv_path)
    rows_received = len(raw_df)
    if rows_received == 0:
        return {
            "canonical_df": pd.DataFrame(),
            "y": pd.Series(dtype=int),
            "threshold": None,
            "rows_received": 0,
            "rows_processed": 0,
            "rows_failed": 0,
        }
    canonical_df, rows_processed, rows_failed = movie_to_canonical(raw_df)
    if rows_processed == 0:
        return {
            "canonical_df": canonical_df,
            "y": pd.Series(dtype=int),
            "threshold": None,
            "rows_received": rows_received,
            "rows_processed": 0,
            "rows_failed": rows_failed,
        }
    y, threshold = compute_label(canonical_df)
    return {
        "canonical_df": canonical_df,
        "y": y,
        "threshold": threshold,
        "rows_received": rows_received,
        "rows_processed": rows_processed,
        "rows_failed": rows_failed,
    }
