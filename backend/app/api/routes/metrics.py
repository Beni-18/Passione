"""GET /metrics

Read straight from the active model's metrics_v{N}.json — never computed or
approximated in the route. Raises MODEL_NOT_READY if no model is loaded yet,
since there is no held-out evaluation to report. Does NOT read the file
itself; that will be model_registry's job once a real bundle is loaded.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.core.errors import ModelNotReadyError
from app.schemas.metrics import MetricsResponse
from app.services.model_registry import model_registry

router = APIRouter()


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics() -> MetricsResponse:
    if not model_registry.is_ready:
        raise ModelNotReadyError("No trained model is loaded; no metrics are available.")

    # Unreachable in phase 1 (is_ready is always False). Real implementation
    # reads model_registry.active_bundle's associated metrics_v{N}.json.
    raise NotImplementedError("Metrics retrieval not implemented until a model is loaded.")
