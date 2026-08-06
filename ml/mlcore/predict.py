"""Inference (plan §1, §12). Model cache, grounded rules, top_features
explanation, response assembly. NEVER raises — a malformed body always
returns a well-formed, contract-shaped, honestly-ungrounded response.
"""
from __future__ import annotations

import json

import joblib
import pandas as pd

from mlcore import config, schema
from mlcore.features import build_features

# --------------------------------------------------------------------------
# Module-level model cache (plan §13's "concurrency contract": read-only
# after load, train_model() writes to a NEW dir and flips latest.json
# atomically, so training-while-serving is safe).
# --------------------------------------------------------------------------
_cache = {
    "loaded": False,
    "model_version": None,
    "pipeline": None,
    "metrics": {},
    "feature_metadata": {},
}


def load_model(version: str | None = None) -> dict:
    """Idempotent. Never raises. Safe to call with no model on disk."""
    try:
        if version is None:
            if not config.LATEST_POINTER_PATH.exists():
                _cache.update(loaded=False, model_version=None, pipeline=None, metrics={}, feature_metadata={})
                return {"loaded": False, "model_version": None, "detail": "No trained model available yet."}
            pointer = json.loads(config.LATEST_POINTER_PATH.read_text())
            version_dir = config.ARTIFACTS_DIR / pointer["model_version"]
        else:
            version_dir = config.ARTIFACTS_DIR / version

        pipe = joblib.load(version_dir / "model.joblib")
        metrics = json.loads((version_dir / "metrics.json").read_text())
        feature_metadata = json.loads((version_dir / "feature_metadata.json").read_text())

        _cache.update(
            loaded=True,
            model_version=metrics.get("model_version", version_dir.name),
            pipeline=pipe,
            metrics=metrics,
            feature_metadata=feature_metadata,
        )
        return {"loaded": True, "model_version": _cache["model_version"], "detail": "Model loaded."}
    except (FileNotFoundError, OSError, json.JSONDecodeError, KeyError) as exc:
        _cache.update(loaded=False, model_version=None, pipeline=None, metrics={}, feature_metadata={})
        return {"loaded": False, "model_version": None, "detail": f"Failed to load model: {exc}"}


def health_check() -> dict:
    """Never raises. ok ONLY if a model is loaded AND passed its metrics gate."""
    if not _cache["loaded"]:
        load_model()  # self-heal if the backend forgot to call load_model() at startup
    loaded = _cache["loaded"]
    passed_gate = bool(_cache["metrics"].get("passed_gate")) if loaded else False
    roc_auc = _cache["metrics"].get("roc_auc") if loaded else None
    if not loaded:
        status, detail = "no_model", "No trained model loaded."
    elif not passed_gate:
        status, detail = "degraded", f"Model loaded but below the honesty gate (ROC-AUC={roc_auc})."
    else:
        status, detail = "ok", f"Model {_cache['model_version']} loaded and passed its metrics gate."
    return {
        "status": status,
        "model_loaded": loaded,
        "model_version": _cache["model_version"],
        "metrics_ok": passed_gate,
        "roc_auc": roc_auc,
        "detail": detail,
    }


def get_model_metadata() -> dict:
    if not _cache["loaded"]:
        load_model()
    m = _cache["metrics"]
    fm = _cache["feature_metadata"]
    return {
        "model_version": _cache["model_version"],
        "algo": m.get("algo"),
        "trained_at": m.get("trained_at"),
        "seed": m.get("seed"),
        "label_strategy": m.get("label_strategy"),
        "features": [f["name"] for f in fm.get("features", [])],
        "metrics": m,
        "n_train": m.get("n_train"),
        "n_test": m.get("n_test"),
        "positive_rate": m.get("positive_rate"),
        "passed_gate": m.get("passed_gate", False),
        "known_categories": fm.get("known_categories", {}),
    }


# --------------------------------------------------------------------------
# top_features explanation (plan §12) — two strategies behind one interface.
# --------------------------------------------------------------------------

def _map_transformed_name(name: str, raw_row: pd.Series) -> tuple[str, str]:
    """Map a preprocessor.get_feature_names_out() name to a (display, value) pair.

    Uses prefix-matching against our known, non-overlapping column name sets
    (cat/num/bool) rather than fragile generic string splitting.
    """
    if name.startswith("cat__"):
        rest = name[len("cat__"):]
        for col in config.CATEGORICAL_FEATURES:
            if rest.startswith(col + "_"):
                value = rest[len(col) + 1:]
                if value == "infrequent_sklearn":
                    value = "other"
                return config.DISPLAY_NAMES.get(col, col), value
        return rest, "?"
    if name.startswith("num__"):
        rest = name[len("num__"):]
        if rest.startswith("missingindicator_"):
            col = rest[len("missingindicator_"):]
            return f"{config.DISPLAY_NAMES.get(col, col)}_missing", "?"
        return config.DISPLAY_NAMES.get(rest, rest), str(raw_row.get(rest, "?"))
    if name.startswith("bool__"):
        rest = name[len("bool__"):]
        return config.DISPLAY_NAMES.get(rest, rest), str(raw_row.get(rest, "?"))
    return name, "?"


def _explain(pipeline, X_row: pd.DataFrame, top_n: int = 3) -> list[str]:
    preprocessor = pipeline.named_steps["preprocess"]
    model = pipeline.named_steps["model"]
    raw_row = X_row.iloc[0]

    try:
        transformed = preprocessor.transform(X_row)[0]
        names = preprocessor.get_feature_names_out()
    except Exception:
        return []

    if hasattr(model, "coef_"):
        weights = model.coef_[0]
        contributions = weights * transformed
    elif hasattr(model, "feature_importances_"):
        # Global importances restricted to features "active" in this row
        # (non-zero one-hot / non-zero-ish numeric) — an honest approximation,
        # not a per-row SHAP-style contribution (plan §12).
        active = transformed != 0
        contributions = model.feature_importances_ * active
    else:
        return []

    ranked = sorted(range(len(names)), key=lambda i: abs(contributions[i]), reverse=True)
    out, seen_display = [], set()
    for i in ranked:
        display, value = _map_transformed_name(names[i], raw_row)
        if value == "?" or display in seen_display:
            continue
        out.append(f"{display}={value}")
        seen_display.add(display)
        if len(out) >= top_n:
            break
    return out


def _confidence_band(confidence: float) -> str:
    if confidence >= 0.75:
        return "high"
    if confidence >= 0.6:
        return "medium"
    return "low"


def predict(metadata: dict) -> dict:
    """THE function. NEVER raises."""
    clean, errors, _ = schema.validate_metadata(metadata)

    if not _cache["loaded"]:
        load_model()

    # --- Rule 1: no model loaded, or loaded model failed the metrics gate ---
    if not _cache["loaded"]:
        return {
            "trending_probability": 0.5, "predicted_label": "uncertain",
            "predicted_label_display": "Uncertain", "confidence": 0.5, "confidence_band": "low",
            "model_version": None, "top_features": [], "grounded": False,
            "reason": "No trained model is loaded.", "errors": errors, "unknown_fields": [],
        }
    if not _cache["metrics"].get("passed_gate", False):
        return {
            "trending_probability": 0.5, "predicted_label": "uncertain",
            "predicted_label_display": "Uncertain", "confidence": 0.5, "confidence_band": "low",
            "model_version": _cache["model_version"], "top_features": [], "grounded": False,
            "reason": "The loaded model did not clear the minimum ROC-AUC gate.",
            "errors": errors, "unknown_fields": [],
        }

    pipeline = _cache["pipeline"]
    known_categories = _cache["feature_metadata"].get("known_categories", {})

    canonical_row = pd.DataFrame([{
        "title": clean["title"], "genre": clean["genre"], "duration_minutes": clean["duration_minutes"],
        "upload_time": clean["upload_time"], "language": clean["language"], "tags": clean["tags"],
    }])
    X_row, _ = build_features(canonical_row)

    # --- Rule 2: unseen category with no fallback encoding -----------------
    unknown_fields = []
    genre_val = X_row["primary_genre"].iloc[0]
    if genre_val not in known_categories.get("primary_genre", []):
        shown = clean["genre"] if clean["genre"] else "missing"
        unknown_fields.append(f"genre={shown}")
    lang_val = X_row["language"].iloc[0]
    if lang_val not in known_categories.get("language", []):
        shown = clean["language"] if clean["language"] else "missing"
        unknown_fields.append(f"language={shown}")

    # --- Rule 3: two or more core fields missing/unparseable ---------------
    missing_core = sum([
        clean["genre"] is None,
        clean["upload_time"] is None,
        clean["language"] is None,
        len(clean["tags"]) == 0,
    ])

    proba = float(pipeline.predict_proba(X_row)[0, 1])
    confidence = max(proba, 1 - proba)
    confidence_band = _confidence_band(confidence)
    top_features = _explain(pipeline, X_row)

    in_uncertain_band = config.UNCERTAIN_BAND[0] <= proba <= config.UNCERTAIN_BAND[1]

    grounded = True
    reason = None
    if unknown_fields:
        grounded = False
        reason = f"Unseen category with no fallback encoding: {', '.join(unknown_fields)}."
    elif missing_core >= 2:
        grounded = False
        reason = "Two or more core fields (genre, upload_time, language, tags) were missing or unparseable."
    elif errors:
        # A required field failed structural validation. Note this can coincide
        # with a genuinely-trained "unknown" bucket (e.g. genre) that would
        # otherwise pass rule 2 — grounded still reflects what the CLIENT sent,
        # not just what the encoder happened to recognize.
        grounded = False
        reason = f"Input validation failed: {'; '.join(errors)}."
    elif in_uncertain_band:
        grounded = False
        reason = f"Predicted probability ({proba:.2f}) falls in the uncertain band."

    predicted_label = "uncertain" if in_uncertain_band else ("trending" if proba >= 0.5 else "not_trending")
    predicted_label_display = {"trending": "Trending", "not_trending": "Not Trending", "uncertain": "Uncertain"}[
        predicted_label
    ]

    return {
        "trending_probability": round(proba, 4),
        "predicted_label": predicted_label,
        "predicted_label_display": predicted_label_display,
        "confidence": round(confidence, 4),
        "confidence_band": confidence_band,
        "model_version": _cache["model_version"],
        "top_features": top_features,
        "grounded": grounded,
        "reason": reason,
        "errors": errors,
        "unknown_fields": unknown_fields,
    }


def predict_batch(items: list[dict]) -> list[dict]:
    return [predict(item) for item in (items or [])]
