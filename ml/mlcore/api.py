"""The ONLY module the backend imports (plan §1, §13).
    from mlcore.api import (
        health_check, load_model, get_model_metadata,
        predict, predict_batch, train_model,
    )
Signatures are frozen as of M0 (T+35). Internals below are DUMMY per handout
§6.2 ("build the pipe before the model") — every function returns a
well-formed, contract-shaped response with grounded=false / canned metrics,
so the backend and frontend can integrate immediately. Internals are swapped
for the real implementation at M4 without changing any signature or shape.
"""
from __future__ import annotations
from typing import Callable

_DUMMY_MODEL_VERSION = "dummy_v0"


def health_check() -> dict:
    """Never raises. Backend maps status -> HTTP for GET /health."""
    return {
        "status": "no_model",
        "model_loaded": False,
        "model_version": None,
        "metrics_ok": False,
        "roc_auc": None,
        "detail": "Dummy pipeline stage (M0) — no model trained yet.",
    }


def load_model(version: str | None = None) -> dict:
    """Idempotent. Safe to call with no model on disk."""
    return {
        "loaded": False,
        "model_version": None,
        "detail": "Dummy pipeline stage (M0) — load_model() is a no-op until training lands.",
    }


def get_model_metadata() -> dict:
    """Everything the UI wants to display about the model itself."""
    return {
        "model_version": None,
        "algo": None,
        "trained_at": None,
        "seed": None,
        "label_strategy": None,
        "features": [],
        "metrics": {},
        "n_train": None,
        "n_test": None,
        "positive_rate": None,
        "passed_gate": False,
        "known_categories": {},
    }


def predict(metadata: dict) -> dict:
    """THE function. NEVER raises — bad input returns grounded=false.
    Dummy stage: always returns a canned, honestly-ungrounded response in the
    exact contract shape, regardless of input, so downstream integration can
    start immediately.
    """
    return {
        "trending_probability": 0.5,
        "predicted_label": "uncertain",
        "predicted_label_display": "Uncertain",
        "confidence": 0.5,
        "confidence_band": "low",
        "model_version": _DUMMY_MODEL_VERSION,
        "top_features": [],
        "grounded": False,
        "reason": "No trained model loaded yet (dummy pipeline stage).",
        "errors": [],
        "unknown_fields": [],
    }


def predict_batch(items: list[dict]) -> list[dict]:
    """Same contract, per item. Errors are per-item, never global."""
    return [predict(item) for item in (items or [])]


def train_model(
    csv_path: str | None = None,
    progress_cb: Callable | None = None,
    seed: int = 42,
    algo: str = "logreg",
) -> dict:
    """Backend runs this in a BackgroundTask and stores the return value for /status.
    Dummy stage: reports a canned "complete" job with zero rows so /status has
    something honest and well-shaped to report immediately.
    """
    if progress_cb:
        progress_cb(0, 0, 0, "complete")
    return {
        "model_version": _DUMMY_MODEL_VERSION,
        "rows_received": 0,
        "rows_processed": 0,
        "rows_failed": 0,
        "metrics": {},
        "artifacts_dir": None,
        "passed_gate": False,
        "promoted": False,
        "status": "complete",
        "detail": "Dummy pipeline stage (M0) — real training lands at M3.",
    }
