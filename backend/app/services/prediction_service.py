"""The grounding decision lives HERE, not in routes/predict.py.

This service is the single call routes/predict.py makes. The actual mlcore
call and threshold application (MIN_ROC_AUC / GROUNDING_MIN_CONFIDENCE) live
in ml_adapter/mlcore_client.py — this module exists so the route never talks
to the adapter directly, per CLAUDE.md section 6 ("routes are thin, call one
service"), and so prediction-specific policy has one obvious home if it
grows beyond what the adapter's generic translation covers.
"""
from __future__ import annotations

from app.ml_adapter.mlcore_client import get_predict_response
from app.schemas.predict import PredictRequest, PredictResponse


def predict(request: PredictRequest) -> PredictResponse:
    return get_predict_response(request)
