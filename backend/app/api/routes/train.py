"""POST /train

Multipart only: a required `file` upload plus an explicit `random_seed`
Form field. Counts real rows, then kicks off training as a background task
— this route returns 202 immediately and never blocks on the run itself.
Does NOT fit anything itself: the background task is
ml_adapter/mlcore_client.run_training, which calls mlcore.train_model()
(docs/INTEGRATION.md Seam 1).

There is deliberately no JSON-body / server-local-path ingestion mode. An
earlier version accepted a bare `csv_path: str` function parameter intending
it as a second, JSON-body mode — FastAPI actually bound it (and
`random_seed`) as query parameters instead, silently breaking both the
documented JSON mode and the documented multipart-form-field mode (the
latter parsed successfully but silently ignored whatever seed was sent,
always using the 42 default). `random_seed: int = Form(...)` below is what
actually makes it bind correctly; do not go back to a bare function
parameter for it.

Hostile-input handling owned here: empty CSV and header-only CSV both raise
EmptyDatasetError before a job is ever created. A missing `file` is a 422
VALIDATION_ERROR, handled automatically by FastAPI since `file` is required.
"""
from __future__ import annotations

import csv

from fastapi import APIRouter, BackgroundTasks, File, Form, UploadFile

from app.core.errors import BadCsvError, EmptyDatasetError
from app.ml_adapter.mlcore_client import run_training
from app.schemas.train import TrainAcceptedResponse
from app.services.job_manager import job_manager
from app.services.training_service import count_csv_rows, persist_uploaded_csv

router = APIRouter()


@router.post("/train", response_model=TrainAcceptedResponse, status_code=202)
async def post_train(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    random_seed: int = Form(42),
) -> TrainAcceptedResponse:
    csv_bytes = await file.read()

    try:
        rows_total = count_csv_rows(csv_bytes)
    except (UnicodeDecodeError, csv.Error):
        raise BadCsvError("Uploaded file could not be parsed as CSV.")

    if rows_total == 0:
        raise EmptyDatasetError("CSV has no data rows (empty file or header-only).")

    record = job_manager.create(rows_total=rows_total)

    # mlcore.train_model() takes a csv_path, not bytes — the upload is
    # written to disk so there's a real path to hand it.
    resolved_csv_path = persist_uploaded_csv(record.job_id, csv_bytes)

    background_tasks.add_task(run_training, record.job_id, resolved_csv_path, random_seed)

    return TrainAcceptedResponse(job_id=record.job_id, rows_received=rows_total, status="queued")
