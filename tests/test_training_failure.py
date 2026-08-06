"""Confirms mlcore.train_model() raising doesn't strand a job at "training".

_safe_train_model in ml_adapter/mlcore_client.py already wraps the call in
try/except and returns a status:"failed" dict with a detail message on any
exception — this test exists to prove that behavior explicitly (not just
assume it), since a silent regression here would mean a training job stuck
at "training" forever with no way for a client to know it died.
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
