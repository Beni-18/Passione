"""Response shape for GET /status.

Does NOT compute rows_processed/rows_failed — those are read verbatim off
job_manager's JobRecord by the route. `metrics` is only populated once
status == "complete".
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from app.schemas.metrics import MetricsResponse


class StatusResponse(BaseModel):
    job_id: str
    status: Literal["queued", "training", "complete", "failed"]
    rows_total: int
    rows_processed: int
    rows_failed: int
    message: str | None = None
    metrics: MetricsResponse | None = None
    model_version: str | None = None
