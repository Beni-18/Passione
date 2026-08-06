"""The grounding decision lives HERE, not in routes/predict.py.

Given a PredictRequest and the current model_registry state, decides:
  - whether a prediction can be made at all (is a model loaded?)
  - whether the input is groundable (known categories, confidence bar)
  - the final grounded/ungrounded PredictResponse

Does NOT do feature engineering — that happens inside the loaded pipeline
(docs/INTEGRATION.md). Does NOT read env vars directly; thresholds come from
core/config.settings.

Phase 1: model_registry is never ready, so every call short-circuits to the
canned ungrounded response required by the skeleton build step. Real
grounding logic (unseen-category checks, confidence threshold) lands once
joblib_loader.py and model_registry are wired to a real bundle.
"""
from __future__ import annotations

from app.core.config import settings
from app.schemas.predict import PredictRequest, PredictResponse
from app.services.model_registry import model_registry


def predict(request: PredictRequest) -> PredictResponse:
    if not model_registry.is_ready:
        return PredictResponse(
            trending_probability=None,
            predicted_label="unknown",
            model_version=model_registry.active_version,
            top_features=[],
            grounded=False,
            reason="No trained model is loaded yet.",
        )

    # Unreachable in phase 1 (is_ready is always False), kept as the shape
    # the real implementation will fill in once a bundle is loaded:
    # unseen-category check against meta.known_categories, then compare
    # predict_proba() confidence against settings.grounding_min_confidence.
    raise NotImplementedError("Real prediction path not implemented until a model is loaded.")
