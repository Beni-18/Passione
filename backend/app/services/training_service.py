"""Orchestrates a training run as a FastAPI background task.

Called by routes/train.py after it has created a JobRecord and returned 202.
Does NOT do any actual model fitting — that lives in ml/src/train.py, a
separate process the ML owner runs. In phase 1 (this skeleton), this module
only simulates the job lifecycle so /status has something real to report
against a fake job: it writes no artifact and trains nothing.

Row-level failures must increment rows_failed and log the row index rather
than aborting the run — that behavior is not yet exercised here since the
skeleton never reads a real CSV row-by-row.
"""
from __future__ import annotations

import csv
import io
import logging

from app.services.job_manager import job_manager

logger = logging.getLogger(__name__)


def count_csv_rows(csv_bytes: bytes) -> int:
    """Returns the number of data rows (excluding header) in a CSV payload."""
    text = io.StringIO(csv_bytes.decode("utf-8"))
    reader = csv.reader(text)
    rows = list(reader)
    if not rows:
        return 0
    return max(0, len(rows) - 1)


async def run_dummy_training(job_id: str) -> None:
    """Phase-1 stand-in for a real training run.

    Immediately marks the job "training" then "complete" with a canned
    metrics payload, so GET /status has a real state machine to report even
    though no model is actually fit. Replaced by a call into ml/ once real
    training lands (build order step 3).
    """
    job_manager.update(job_id, status="training")

    record = job_manager.get(job_id)
    if record is None:
        logger.error("run_dummy_training called for unknown job_id=%s", job_id)
        return

    dummy_metrics = {
        "model_version": "stub_v0",
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "roc_auc": 0.0,
        "accuracy": 0.0,
        "positive_rate": 0.0,
        "random_seed": 42,
        "split": {"train": 0, "val": 0, "test": 0},
        "trained_at": "1970-01-01T00:00:00Z",
    }

    job_manager.update(
        job_id,
        status="complete",
        rows_processed=record.rows_total,
        rows_failed=0,
        model_version="stub_v0",
        metrics=dummy_metrics,
        message="Dummy training run (phase 1 skeleton) — no model was fit.",
    )
