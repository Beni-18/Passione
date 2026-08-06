"""GET /status?job_id=...

Reads real counts straight off job_manager's JobRecord — never hardcodes
progress. Raises JobNotFoundError for an unknown job_id. Does NOT run or
advance training itself; that happens in the background task started by
POST /train.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.core.errors import JobNotFoundError
from app.schemas.metrics import MetricsResponse
from app.schemas.status import StatusResponse
from app.services.job_manager import job_manager

router = APIRouter()


@router.get("/status", response_model=StatusResponse)
async def get_status(job_id: str) -> StatusResponse:
    record = job_manager.get(job_id)
    if record is None:
        raise JobNotFoundError(f"No job found with id {job_id!r}.")

    metrics = MetricsResponse(**record.metrics) if record.metrics else None

    return StatusResponse(
        job_id=record.job_id,
        status=record.status,
        rows_total=record.rows_total,
        rows_processed=record.rows_processed,
        rows_failed=record.rows_failed,
        message=record.message,
        metrics=metrics,
        model_version=record.model_version,
    )
