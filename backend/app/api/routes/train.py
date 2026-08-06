"""POST /train

Accepts either a JSON body {"csv_path": ..., "random_seed": ...} or a
multipart file upload, counts real rows, and kicks off training as a
background task — this route returns 202 immediately and never blocks on
the run itself. Does NOT do any fitting itself; that's training_service.py
(phase 1: a dummy run) and eventually ml/src/train.py.

Hostile-input handling owned here: empty CSV and header-only CSV both raise
EmptyDatasetError before a job is ever created.
"""
from __future__ import annotations

import csv
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, UploadFile

from app.core.errors import BadCsvError, EmptyDatasetError
from app.schemas.train import TrainAcceptedResponse
from app.services.job_manager import job_manager
from app.services.training_service import count_csv_rows, run_dummy_training

router = APIRouter()


@router.post("/train", response_model=TrainAcceptedResponse, status_code=202)
async def post_train(
    background_tasks: BackgroundTasks,
    file: UploadFile | None = None,
    csv_path: str | None = None,
    random_seed: int = 42,
) -> TrainAcceptedResponse:
    if file is not None:
        csv_bytes = await file.read()
    elif csv_path is not None:
        path = Path(csv_path)
        if not path.is_file():
            raise BadCsvError(f"csv_path does not exist: {csv_path}")
        csv_bytes = path.read_bytes()
    else:
        raise BadCsvError("Provide either a multipart 'file' or a JSON 'csv_path'.")

    try:
        rows_total = count_csv_rows(csv_bytes)
    except (UnicodeDecodeError, csv.Error):
        raise BadCsvError("Uploaded file could not be parsed as CSV.")

    if rows_total == 0:
        raise EmptyDatasetError("CSV has no data rows (empty file or header-only).")

    record = job_manager.create(rows_total=rows_total)
    background_tasks.add_task(run_dummy_training, record.job_id)

    return TrainAcceptedResponse(job_id=record.job_id, rows_received=rows_total, status="queued")
