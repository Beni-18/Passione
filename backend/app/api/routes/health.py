"""GET /health

Returns "ok" only when a trained model is loaded and cleared MIN_ROC_AUC;
"degraded" otherwise. Does NOT itself decide readiness — that's
model_registry.is_ready. A started container is not a ready service.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.schemas.health import HealthResponse
from app.services.enrichment import is_enrichment_api_connected
from app.services.model_registry import model_registry

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    enrichment_connected = await is_enrichment_api_connected()
    return HealthResponse(
        status="ok" if model_registry.is_ready else "degraded",
        model_loaded=model_registry.is_ready,
        model_version=model_registry.active_version,
        enrichment_api_connected=enrichment_connected,
    )
