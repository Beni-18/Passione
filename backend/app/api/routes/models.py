"""GET /models, POST /models/activate

Lists discovered model versions and lets a bad retrain be rolled back
without retraining by switching the active version. Does NOT discover or
load artifacts itself — that's model_registry.py.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.core.errors import ModelNotReadyError
from app.schemas.models import ActivateModelRequest, ActiveModelResponse, ModelListResponse
from app.services.model_registry import model_registry

router = APIRouter()


@router.get("/models", response_model=ModelListResponse)
async def get_models() -> ModelListResponse:
    return ModelListResponse(
        active=model_registry.active_version,
        available=model_registry.available_versions,
    )


@router.post("/models/activate", response_model=ActiveModelResponse)
async def post_models_activate(request: ActivateModelRequest) -> ActiveModelResponse:
    try:
        active = model_registry.activate(request.model_version)
    except NotImplementedError as exc:
        raise ModelNotReadyError(str(exc))
    return ActiveModelResponse(active=active)
