"""Asserts response shapes match docs/API_CONTRACT.md.

Phase 1: only exercises the shapes reachable without a trained model
(health degraded, train/status happy path, predict/metrics both 409 since
the service isn't ready). Grounded/ungrounded PredictResponse shapes are
covered in tests/test_grounding_ownership.py via a monkeypatched mlcore,
since the real dummy mlcore never reports a ready service.
"""
from __future__ import annotations

import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_shape_degraded():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body == {
        "status": "degraded",
        "model_loaded": False,
        "model_version": None,
        "enrichment_api_connected": False,
    }


def test_train_then_status_shape():
    csv_bytes = b"title,genre,duration_minutes,upload_time,language,tags\nA,Comedy,10,2026-01-01T00:00:00Z,en,tag1\n"
    train_response = client.post(
        "/train", files={"file": ("data.csv", io.BytesIO(csv_bytes), "text/csv")}
    )
    assert train_response.status_code == 202
    train_body = train_response.json()
    assert set(train_body) == {"job_id", "rows_received", "status"}
    assert train_body["rows_received"] == 1
    assert train_body["status"] == "queued"

    status_response = client.get("/status", params={"job_id": train_body["job_id"]})
    assert status_response.status_code == 200
    status_body = status_response.json()
    assert set(status_body) == {
        "job_id", "status", "rows_total", "rows_processed",
        "rows_failed", "message", "metrics", "model_version",
    }


def test_predict_not_ready():
    response = client.post(
        "/predict",
        json={
            "title": "Midnight Run",
            "genre": "Thriller",
            "duration_minutes": 24,
            "upload_time": "2026-08-06T18:30:00Z",
            "language": "en",
            "tags": ["suspense"],
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "MODEL_NOT_READY"


def test_metrics_not_ready():
    response = client.get("/metrics")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "MODEL_NOT_READY"
