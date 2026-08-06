"""The single call routes/predict.py makes.

The grounding decision itself belongs to mlcore, not to this service —
`grounded`/`predicted_label`/`reason` pass through from mlcore's predict()
unmodified. What lives in ml_adapter/mlcore_client.py is the readiness gate
(MIN_ROC_AUC — is a model even loaded and fit to call?) and the dict→schema
translation. This module exists so the route never talks to the adapter
directly, per CLAUDE.md section 6 ("routes are thin, call one service"), and
so prediction-specific policy has one obvious home if it grows beyond what
the adapter's generic translation covers.
"""
from __future__ import annotations

from app.ml_adapter.mlcore_client import get_predict_response
from app.schemas.predict import PredictRequest, PredictResponse


def predict(request: PredictRequest) -> PredictResponse:
    return get_predict_response(request)
