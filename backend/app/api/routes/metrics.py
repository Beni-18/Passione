"""GET /metrics

Read from mlcore.get_model_metadata() via ml_adapter/mlcore_client.py, which
also applies MIN_ROC_AUC before returning anything — a model that trained
but didn't clear the bar produces the same MODEL_NOT_READY as no model at
all, since there is no trustworthy held-out evaluation to report either way.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.core.errors import ModelNotReadyError
from app.ml_adapter.mlcore_client import get_metrics_response
from app.schemas.metrics import MetricsResponse

router = APIRouter()


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics() -> MetricsResponse:
    metrics = get_metrics_response()
    if metrics is None:
        raise ModelNotReadyError("No trained model is loaded; no metrics are available.")
    return metrics
