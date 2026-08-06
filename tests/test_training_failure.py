"""Confirms mlcore.train_model() failures don't strand a job at "training",
in two distinct ways:

  - mlcore.train_model() itself raising: _safe_train_model in
    ml_adapter/mlcore_client.py already wraps the call in try/except and
    returns a status:"failed" dict with a detail message.
  - mlcore.train_model() returning successfully but with a metrics dict
    shaped so badly that building a MetricsResponse out of it raises (e.g.
    a non-numeric roc_auc) — this happens *after* _safe_train_model returns,
    inside run_training's own field-mapping step, and is only caught by the
    try/except run_training wraps its whole body in.
"""
from __future__ import annotations

import io

from fastapi.testclient import TestClient

from app.main import app
import app.ml_adapter.mlcore_client as mlcore_client

client = TestClient(app)


def test_status_reports_failed_when_mlcore_train_model_raises(monkeypatch):
    def _raise(*args, **kwargs):
        raise RuntimeError("simulated mlcore training crash")

    monkeypatch.setattr(mlcore_client, "train_model", _raise)

    csv_bytes = b"title,genre,duration_minutes,upload_time,language,tags\nA,Comedy,10,2026-01-01T00:00:00Z,en,tag1\n"
    train_response = client.post(
        "/train", files={"file": ("data.csv", io.BytesIO(csv_bytes), "text/csv")}
    )
    assert train_response.status_code == 202
    job_id = train_response.json()["job_id"]

    status_response = client.get("/status", params={"job_id": job_id})
    assert status_response.status_code == 200
    body = status_response.json()
    assert body["status"] == "failed"
    assert body["message"]
    assert "simulated mlcore training crash" in body["message"]


def test_status_reports_failed_when_metrics_shape_is_malformed(monkeypatch):
    def _malformed_metrics(csv_path=None, progress_cb=None, seed=42, algo="logreg"):
        if progress_cb:
            progress_cb(50, 0, 50, "complete")
        return {
            "model_version": "rf_v1",
            "rows_received": 50,
            "rows_processed": 50,
            "rows_failed": 0,
            # roc_auc is a non-numeric string — MetricsResponse's field is a
            # float, so building a response from this must raise, not
            # silently coerce or crash the whole process.
            "metrics": {"roc_auc": "not-a-number", "precision": 0.5},
            "artifacts_dir": None,
            "passed_gate": True,
            "promoted": True,
            "status": "complete",
            "detail": None,
        }

    monkeypatch.setattr(mlcore_client, "train_model", _malformed_metrics)

    csv_bytes = b"title,genre,duration_minutes,upload_time,language,tags\nA,Comedy,10,2026-01-01T00:00:00Z,en,tag1\n"
    train_response = client.post(
        "/train", files={"file": ("data.csv", io.BytesIO(csv_bytes), "text/csv")}
    )
    assert train_response.status_code == 202
    job_id = train_response.json()["job_id"]

    status_response = client.get("/status", params={"job_id": job_id})
    assert status_response.status_code == 200
    body = status_response.json()
    assert body["status"] == "failed"
    assert body["message"]
    assert "Training failed while recording results" in body["message"]
