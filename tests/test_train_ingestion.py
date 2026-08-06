"""POST /train's request binding — regression coverage for a bug where
csv_path/random_seed were bound as query parameters by FastAPI's default
inference instead of multipart form fields, so a client-supplied seed was
silently discarded in favor of the 42 default (see routes/train.py).
"""
from __future__ import annotations

import io

from fastapi.testclient import TestClient

from app.main import app
import app.api.routes.train as train_route

client = TestClient(app)

_CSV_BYTES = b"title,genre,duration_minutes,upload_time,language,tags\nA,Comedy,10,2026-01-01T00:00:00Z,en,tag1\n"


def test_random_seed_form_field_reaches_run_training(monkeypatch):
    captured: dict = {}

    def spy(job_id, csv_path, seed, algo="logreg"):
        captured["seed"] = seed

    monkeypatch.setattr(train_route, "run_training", spy)

    response = client.post(
        "/train",
        files={"file": ("d.csv", io.BytesIO(_CSV_BYTES), "text/csv")},
        data={"random_seed": "777"},
    )

    assert response.status_code == 202
    assert captured["seed"] == 777  # not the 42 default


def test_random_seed_defaults_to_42_when_omitted(monkeypatch):
    captured: dict = {}

    def spy(job_id, csv_path, seed, algo="logreg"):
        captured["seed"] = seed

    monkeypatch.setattr(train_route, "run_training", spy)

    response = client.post("/train", files={"file": ("d.csv", io.BytesIO(_CSV_BYTES), "text/csv")})

    assert response.status_code == 202
    assert captured["seed"] == 42


def test_missing_file_is_validation_error():
    response = client.post("/train")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
