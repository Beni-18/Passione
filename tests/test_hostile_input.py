"""The five hostile cases from CLAUDE.md section 7 — each must return a
clean 4xx with the error envelope, never a stack trace or a dead container.
"""
from __future__ import annotations

import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _assert_error_envelope(response, expected_status: int, expected_code: str):
    assert response.status_code == expected_status
    body = response.json()
    assert "error" in body
    assert body["error"]["code"] == expected_code


def test_empty_training_csv():
    response = client.post(
        "/train", files={"file": ("empty.csv", io.BytesIO(b""), "text/csv")}
    )
    _assert_error_envelope(response, 400, "EMPTY_DATASET")


def test_header_only_training_csv():
    csv_bytes = b"title,genre,duration_minutes,upload_time,language,tags\n"
    response = client.post(
        "/train", files={"file": ("header_only.csv", io.BytesIO(csv_bytes), "text/csv")}
    )
    _assert_error_envelope(response, 400, "EMPTY_DATASET")


def test_predict_missing_required_field():
    response = client.post(
        "/predict",
        json={
            "title": "Midnight Run",
            "genre": "Thriller",
            # duration_minutes deliberately omitted
            "upload_time": "2026-08-06T18:30:00Z",
            "language": "en",
            "tags": [],
        },
    )
    _assert_error_envelope(response, 422, "VALIDATION_ERROR")


def test_predict_unseen_category_before_any_model_trained():
    # No model is trained anywhere in this test module, so this exercises
    # the "no model loaded" path rather than a real unseen-category check —
    # that distinction only exists once mlcore has a real model loaded and
    # reports grounded=false for an unseen category specifically. Both
    # currently resolve to grounded: false via the same dummy mlcore stage.
    response = client.post(
        "/predict",
        json={
            "title": "Kuchipudi Dreams",
            "genre": "Kuchipudi-Fusion",
            "duration_minutes": 18,
            "upload_time": "2026-08-06T18:30:00Z",
            "language": "en",
            "tags": ["dance"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["grounded"] is False
    assert body["reason"]


def test_predict_before_any_model_trained():
    response = client.post(
        "/predict",
        json={
            "title": "Midnight Run",
            "genre": "Thriller",
            "duration_minutes": 24,
            "upload_time": "2026-08-06T18:30:00Z",
            "language": "en",
            "tags": [],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["grounded"] is False
    assert body["trending_probability"] is None
    assert body["predicted_label"] == "unknown"
    assert body["reason"]
