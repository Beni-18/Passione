"""In-memory registry of training jobs, keyed by job_id.

The single source of truth for row counts and status that GET /status reads.
Does NOT run training itself — training_service.py does the work and calls
back into this registry to update progress. Does NOT persist to disk: job
history is lost on restart, which is acceptable for this build (jobs are
short-lived and re-triggerable).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

JobStatus = Literal["queued", "training", "complete", "failed"]


@dataclass
class JobRecord:
    job_id: str
    status: JobStatus = "queued"
    rows_total: int = 0
    rows_processed: int = 0
    rows_failed: int = 0
    message: str | None = None
    model_version: str | None = None
    metrics: dict | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}

    def create(self, rows_total: int) -> JobRecord:
        job_id = uuid.uuid4().hex[:8]
        record = JobRecord(job_id=job_id, rows_total=rows_total)
        self._jobs[job_id] = record
        return record

    def get(self, job_id: str) -> JobRecord | None:
        return self._jobs.get(job_id)

    def update(self, job_id: str, **fields) -> JobRecord | None:
        record = self._jobs.get(job_id)
        if record is None:
            return None
        for key, value in fields.items():
            setattr(record, key, value)
        return record


# Process-wide singleton. Fine for a single-container deployment; would need
# to move to shared storage if the API ever runs multiple replicas.
job_manager = JobManager()
