"""The ONLY file in backend/ that imports mlcore.

Wraps every one of mlcore's six frozen functions (health_check, load_model,
get_model_metadata, predict, predict_batch, train_model — docs/INTEGRATION.md
Seam 1) in try/except: an unexpected exception here becomes the same
grounded:false / degraded shape a normal ungrounded response would produce,
never a 500. Also translates mlcore's raw dicts into our Pydantic schemas
(app/schemas/*).

Ownership split (do not blur this):
  - mlcore owns prediction semantics. `grounded`, `predicted_label`,
    `reason` pass through from mlcore's predict() response unmodified — no
    backend recomputation, no second confidence threshold. mlcore's
    `grounded` claim is final.
  - The backend owns service readiness only, via MIN_ROC_AUC: it gates
    `/health`'s status and gates whether `/predict` is even attempted —
    if the service isn't ready, get_predict_response raises
    ModelNotReadyError before calling mlcore.predict() at all, rather than
    calling it and second-guessing the result.

Does NOT do any feature engineering, training, or model loading itself —
all of that is inside mlcore. Does NOT change PredictResponse/HealthResponse/
etc. field names to match mlcore's dict keys — every field is mapped
explicitly below, by name, so mlcore's internal vocabulary never leaks
through this boundary (the one exception being predicted_label's vocabulary,
which is coerced to fit our schema's Literal — see _LABEL_MAP below; that
coercion is a schema-fit, not a semantic override of mlcore's decision).
"""
from __future__ import annotations

import logging
from typing import Callable

from mlcore.api import (
    get_model_metadata,
    health_check,
    load_model,
    predict,
    predict_batch,
    train_model,
)

from app.core.config import settings
from app.core.errors import ModelNotReadyError
from app.schemas.health import HealthResponse
from app.schemas.metrics import MetricsResponse, SplitCounts
from app.schemas.models import ActiveModelResponse, ModelListResponse
from app.schemas.predict import PredictRequest, PredictResponse
from app.services.job_manager import job_manager

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Layer 1: raw, exception-safe calls into mlcore. Each returns a dict shaped
# exactly like mlcore's own contract — callers below never see an exception
# and never see a shape mlcore wouldn't itself produce.
# ---------------------------------------------------------------------------

def _safe_health_check() -> dict:
    try:
        return health_check()
    except Exception as exc:  # mlcore's "never raises" is not trusted here.
        logger.exception("mlcore.health_check() raised unexpectedly")
        return {
            "status": "no_model",
            "model_loaded": False,
            "model_version": None,
            "metrics_ok": False,
            "roc_auc": None,
            "detail": f"Adapter caught an unexpected error from mlcore: {exc}",
        }


def _safe_get_model_metadata() -> dict:
    try:
        return get_model_metadata()
    except Exception as exc:
        logger.exception("mlcore.get_model_metadata() raised unexpectedly")
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


def _safe_load_model(version: str | None = None) -> dict:
    try:
        return load_model(version)
    except Exception as exc:
        logger.exception("mlcore.load_model(%r) raised unexpectedly", version)
        return {
            "loaded": False,
            "model_version": None,
            "detail": f"Adapter caught an unexpected error from mlcore: {exc}",
        }


def _predict_error_fallback(exc: Exception) -> dict:
    return {
        "trending_probability": None,
        "predicted_label": "uncertain",
        "predicted_label_display": "Uncertain",
        "confidence": 0.0,
        "confidence_band": "low",
        "model_version": None,
        "top_features": [],
        "grounded": False,
        "reason": f"Adapter caught an unexpected error from mlcore: {exc}",
        "errors": [str(exc)],
        "unknown_fields": [],
    }


def _safe_predict(metadata: dict) -> dict:
    try:
        return predict(metadata)
    except Exception as exc:
        logger.exception("mlcore.predict() raised unexpectedly")
        return _predict_error_fallback(exc)


def _safe_predict_batch(items: list[dict]) -> list[dict]:
    try:
        return predict_batch(items)
    except Exception as exc:
        logger.exception("mlcore.predict_batch() raised unexpectedly")
        return [_predict_error_fallback(exc) for _ in items]


def _safe_train_model(
    csv_path: str | None,
    progress_cb: Callable | None,
    seed: int,
    algo: str,
) -> dict:
    try:
        return train_model(csv_path=csv_path, progress_cb=progress_cb, seed=seed, algo=algo)
    except Exception as exc:
        logger.exception("mlcore.train_model() raised unexpectedly")
        return {
            "model_version": None,
            "rows_received": 0,
            "rows_processed": 0,
            "rows_failed": 0,
            "metrics": {},
            "artifacts_dir": None,
            "passed_gate": False,
            "promoted": False,
            "status": "failed",
            "detail": f"Adapter caught an unexpected error from mlcore: {exc}",
        }


# ---------------------------------------------------------------------------
# Layer 2: translation into our Pydantic schemas + our readiness policy.
# MIN_ROC_AUC is the only threshold applied here — it gates /health and
# whether /predict is attempted at all. It never overrides mlcore's own
# per-prediction grounding decision.
# ---------------------------------------------------------------------------

def _roc_auc_clears_bar(roc_auc: float | None) -> bool:
    return roc_auc is not None and roc_auc >= settings.min_roc_auc


def _is_service_ready() -> bool:
    """True only when mlcore reports a loaded model whose roc_auc clears
    MIN_ROC_AUC — the same definition /health uses. Gates whether /predict
    is attempted at all.
    """
    raw = _safe_health_check()
    return bool(raw.get("model_loaded")) and _roc_auc_clears_bar(raw.get("roc_auc"))


def get_health_response(enrichment_api_connected: bool) -> HealthResponse:
    raw = _safe_health_check()
    is_ready = bool(raw.get("model_loaded")) and _roc_auc_clears_bar(raw.get("roc_auc"))
    return HealthResponse(
        status="ok" if is_ready else "degraded",
        model_loaded=bool(raw.get("model_loaded")),
        model_version=raw.get("model_version"),
        enrichment_api_connected=enrichment_api_connected,
    )


def get_metrics_response() -> MetricsResponse | None:
    """Returns None if no model is ready — callers raise ModelNotReadyError."""
    raw = _safe_get_model_metadata()
    metrics = raw.get("metrics") or {}
    roc_auc = metrics.get("roc_auc")

    if not raw.get("passed_gate") or roc_auc is None or roc_auc < settings.min_roc_auc:
        return None
    if raw.get("model_version") is None:
        return None

    # mlcore reports n_train/n_test but no validation-split count — our
    # schema's split.val has no mlcore source yet, so it defaults to 0.
    # Flagged here rather than silently guessed: revisit once mlcore's
    # metrics shape is finalized at M3/M4.
    return MetricsResponse(
        model_version=raw["model_version"],
        precision=metrics.get("precision", 0.0),
        recall=metrics.get("recall", 0.0),
        f1=metrics.get("f1", 0.0),
        roc_auc=roc_auc,
        accuracy=metrics.get("accuracy", 0.0),
        positive_rate=raw.get("positive_rate") or 0.0,
        random_seed=raw.get("seed") or 0,
        split=SplitCounts(train=raw.get("n_train") or 0, val=0, test=raw.get("n_test") or 0),
        trained_at=raw.get("trained_at") or "",
    )


def get_models_response() -> ModelListResponse:
    """mlcore exposes no "list all versions" call (only the six frozen
    functions), so "available" can only ever contain the currently loaded
    version, if any — not real version history. Documented limitation, not
    an oversight: see docs/INTEGRATION.md Seam 1.
    """
    raw = _safe_get_model_metadata()
    version = raw.get("model_version")
    return ModelListResponse(active=version, available=[version] if version else [])


def activate_model(model_version: str) -> ActiveModelResponse:
    raw = _safe_load_model(model_version)
    if not raw.get("loaded"):
        raise ModelNotReadyError(raw.get("detail") or f"Could not activate model {model_version!r}.")
    return ActiveModelResponse(active=raw.get("model_version") or model_version)


# Schema-fit only: our PredictResponse.predicted_label is a Literal that
# doesn't include mlcore's "uncertain" value. This does not decide grounding
# or reinterpret mlcore's answer — it only maps vocabulary so the response
# validates. grounded/reason are never touched here.
_LABEL_MAP = {"trending": "trending", "not_trending": "not_trending"}


def get_predict_response(request: PredictRequest) -> PredictResponse:
    if not _is_service_ready():
        raise ModelNotReadyError(
            "No trained model is loaded, or its metrics haven't cleared MIN_ROC_AUC."
        )

    payload = request.model_dump(mode="json")
    raw = _safe_predict(payload)

    grounded = bool(raw.get("grounded"))

    return PredictResponse(
        trending_probability=raw.get("trending_probability") if grounded else None,
        predicted_label=_LABEL_MAP.get(raw.get("predicted_label"), "unknown"),
        model_version=raw.get("model_version"),
        top_features=(raw.get("top_features") or []) if grounded else [],
        grounded=grounded,
        reason=raw.get("reason"),
    )


def run_training(job_id: str, csv_path: str, seed: int, algo: str = "logreg") -> None:
    """Runs mlcore.train_model as the /train background task, wiring
    progress_cb into job_manager so /status has real counts (Seam 1 rule 4).
    Never raises: _safe_train_model already catches everything.
    """
    job_manager.update(job_id, status="training")

    def progress_cb(processed: int, failed: int, total: int, status: str) -> None:
        updates: dict = {"rows_processed": processed, "rows_failed": failed, "status": status}
        if total:
            # Only trust mlcore's total once it reports a real (non-zero)
            # count — the dummy stage always reports 0, and overwriting our
            # own upload-time row count with that would be a regression.
            updates["rows_total"] = total
        job_manager.update(job_id, **updates)

    result = _safe_train_model(csv_path=csv_path, progress_cb=progress_cb, seed=seed, algo=algo)

    job_manager.update(
        job_id,
        status=result.get("status", "failed"),
        rows_processed=result.get("rows_processed", 0),
        rows_failed=result.get("rows_failed", 0),
        model_version=result.get("model_version"),
        metrics=result.get("metrics") or None,
        message=result.get("detail"),
    )
