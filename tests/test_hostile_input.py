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


def test_predict_with_unseen_category_before_any_model_trained():
    # No model is trained anywhere in this test module, so the MIN_ROC_AUC
    # readiness gate in ml_adapter/mlcore_client.py rejects this before
    # mlcore.predict() is ever called — it's indistinguishable from any
    # other "no model loaded" case at this stage. A real unseen-category
    # grounded:false response (once a model IS loaded) is covered by
    # tests/test_grounding_ownership.py via a monkeypatched mlcore.
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
    _assert_error_envelope(response, 409, "MODEL_NOT_READY")


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
    _assert_error_envelope(response, 409, "MODEL_NOT_READY")
