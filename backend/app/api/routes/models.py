"""GET /models, POST /models/activate

Both delegate to ml_adapter/mlcore_client.py, which calls mlcore's
get_model_metadata()/load_model(). Note: mlcore exposes no "list all
versions" call among its six frozen functions, so `available` can only ever
reflect the currently loaded version, not real version history — see
mlcore_client.get_models_response()'s docstring.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.ml_adapter.mlcore_client import activate_model, get_models_response
from app.schemas.models import ActivateModelRequest, ActiveModelResponse, ModelListResponse

router = APIRouter()


@router.get("/models", response_model=ModelListResponse)
async def get_models() -> ModelListResponse:
    return get_models_response()


@router.post("/models/activate", response_model=ActiveModelResponse)
async def post_models_activate(request: ActivateModelRequest) -> ActiveModelResponse:
    return activate_model(request.model_version)
