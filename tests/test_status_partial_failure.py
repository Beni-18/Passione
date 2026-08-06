"""GET /status's row counts against a training run that partially fails,
and against one still in flight — both paths the real dummy mlcore can't
produce (it always reports 0/0/0 and "complete" immediately), so mlcore's
train_model is monkeypatched directly (same pattern as
tests/test_training_failure.py).
"""
from __future__ import annotations

import io
from pathlib import Path

from fastapi.testclient import TestClient

import app.ml_adapter.mlcore_client as mlcore_client
from app.main import app

client = TestClient(app)

_CSV_BYTES = b"title,genre,duration_minutes,upload_time,language,tags\nA,Comedy,10,2026-01-01T00:00:00Z,en,tag1\n"


def _post_train() -> str:
    response = client.post("/train", files={"file": ("d.csv", io.BytesIO(_CSV_BYTES), "text/csv")})
    assert response.status_code == 202
    return response.json()["job_id"]


def test_status_reports_exact_counts_on_partial_row_failure(monkeypatch):
    def _train_model(csv_path=None, progress_cb=None, seed=42, algo="logreg"):
        if progress_cb:
            progress_cb(80, 20, 100, "complete")
        return {
            "model_version": "rf_v1",
            "rows_received": 100,
            "rows_processed": 80,
            "rows_failed": 20,
            "metrics": {},
            "artifacts_dir": None,
            "passed_gate": False,
            "promoted": False,
            "status": "complete",
            "detail": None,
        }

    monkeypatch.setattr(mlcore_client, "train_model", _train_model)

    job_id = _post_train()
    status = client.get("/status", params={"job_id": job_id}).json()

    assert status["status"] == "complete"
    assert status["rows_total"] == 100
    assert status["rows_processed"] == 80
    assert status["rows_failed"] == 20
    assert status["rows_processed"] + status["rows_failed"] == status["rows_total"]


def test_status_reports_training_while_still_in_flight(monkeypatch):
    mid_run_status: dict = {}

    def _train_model(csv_path=None, progress_cb=None, seed=42, algo="logreg"):
        # Everything in this test suite runs synchronously (TestClient
        # executes background tasks inline), so querying /status from
        # inside this callback, before it returns, genuinely captures the
        # state a concurrent poller would see mid-run.
        job_id = Path(csv_path).stem
        if progress_cb:
            progress_cb(30, 5, 100, "training")
        mid_run_status.update(client.get("/status", params={"job_id": job_id}).json())

        return {
            "model_version": "rf_v1",
            "rows_received": 100,
            "rows_processed": 100,
            "rows_failed": 0,
            "metrics": {},
            "artifacts_dir": None,
            "passed_gate": False,
            "promoted": False,
            "status": "complete",
            "detail": None,
        }

    monkeypatch.setattr(mlcore_client, "train_model", _train_model)

    job_id = _post_train()

    assert mid_run_status["status"] == "training"
    assert mid_run_status["rows_processed"] == 30
    assert mid_run_status["rows_failed"] == 5
    assert mid_run_status["rows_total"] == 100
    assert mid_run_status["rows_processed"] + mid_run_status["rows_failed"] < mid_run_status["rows_total"]

    # After the background task finishes, the final state reflects completion.
    final_status = client.get("/status", params={"job_id": job_id}).json()
    assert final_status["status"] == "complete"
    assert final_status["rows_processed"] == 100
    assert final_status["rows_failed"] == 0
