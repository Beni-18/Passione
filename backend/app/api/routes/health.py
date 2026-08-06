"""GET /health

Returns "ok" only when mlcore reports a loaded model AND its roc_auc clears
MIN_ROC_AUC — that threshold check happens in ml_adapter/mlcore_client.py,
not here. A started container is not a ready service.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.ml_adapter.mlcore_client import get_health_response
from app.schemas.health import HealthResponse
from app.services.enrichment import is_enrichment_api_connected

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    enrichment_connected = await is_enrichment_api_connected()
    return get_health_response(enrichment_connected)
