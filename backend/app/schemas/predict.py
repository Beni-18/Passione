"""Request/response shapes for POST /predict.

Field names in PredictRequest are exactly the six raw fields the ML pipeline
expects (docs/INTEGRATION.md) — the backend must never rename or derive new
fields onto this model, since it is passed straight through to
pipeline.transform() as a DataFrame. Does NOT decide `grounded` — that is
prediction_service.py's job; this file only shapes the wire payload.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    title: str
    genre: str
    duration_minutes: int = Field(gt=0)
    upload_time: datetime
    language: str
    tags: list[str] = Field(default_factory=list)


class PredictResponse(BaseModel):
    trending_probability: float | None
    predicted_label: Literal["trending", "not_trending", "unknown"]
    model_version: str | None
    top_features: list[str]
    grounded: bool
    reason: str | None = None
