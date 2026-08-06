"""POST /predict

Validates the request shape and delegates entirely to
prediction_service.predict — the grounding decision does NOT live here.
This route body is intentionally under 15 lines per section 6.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.schemas.predict import PredictRequest, PredictResponse
from app.services.prediction_service import predict as predict_service

router = APIRouter()


@router.post("/predict", response_model=PredictResponse)
async def post_predict(request: PredictRequest) -> PredictResponse:
    return predict_service(request)
