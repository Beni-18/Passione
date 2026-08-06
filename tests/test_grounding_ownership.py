"""Regression tests for the ownership split in ml_adapter/mlcore_client.py:

  - mlcore owns prediction semantics: grounded, predicted_label, reason
    pass through from predict() unmodified — no backend recomputation
    against a confidence threshold.
  - The backend owns service readiness only, via MIN_ROC_AUC: /predict is
    never attempted (mlcore.predict() is never called) unless the service
    is ready.

Both are exercised here by monkeypatching mlcore's health_check/predict
directly, since the real dummy mlcore never reports a ready service.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

import app.ml_adapter.mlcore_client as mlcore_client
from app.main import app

client = TestClient(app)


def _make_ready_health_check():
    return lambda: {
        "status": "ready",
        "model_loaded": True,
        "model_version": "rf_v3",
        "metrics_ok": True,
        "roc_auc": 0.90,
        "detail": None,
    }


_PREDICT_PAYLOAD = {
    "title": "Midnight Run",
    "genre": "Thriller",
    "duration_minutes": 24,
    "upload_time": "2026-08-06T18:30:00Z",
    "language": "en",
    "tags": ["suspense"],
}


def test_ungrounded_passes_through_even_with_high_confidence(monkeypatch):
    # confidence is deliberately far above the old (now-removed)
    # GROUNDING_MIN_CONFIDENCE default of 0.60 — if the backend were still
    # recomputing grounded from confidence, this would flip to True. It
    # must not: mlcore said grounded=False, and that's final.
    monkeypatch.setattr(mlcore_client, "health_check", _make_ready_health_check())
    monkeypatch.setattr(
        mlcore_client,
        "predict",
        lambda metadata: {
            "trending_probability": 0.42,
            "predicted_label": "uncertain",
            "predicted_label_display": "Uncertain",
            "confidence": 0.99,
            "confidence_band": "high",
            "model_version": "rf_v3",
            "top_features": [],
            "grounded": False,
            "reason": "Unseen genre 'Kuchipudi-Fusion' — no fallback encoding.",
            "errors": [],
            "unknown_fields": [],
        },
    )

    response = client.post("/predict", json=_PREDICT_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["grounded"] is False
    assert body["reason"] == "Unseen genre 'Kuchipudi-Fusion' — no fallback encoding."
    assert body["trending_probability"] is None


def test_grounded_passes_through_even_with_low_confidence(monkeypatch):
    # confidence is deliberately far below the old GROUNDING_MIN_CONFIDENCE
    # default — if the backend still second-guessed mlcore, this would flip
    # to False. It must not: mlcore said grounded=True, and that's final.
    monkeypatch.setattr(mlcore_client, "health_check", _make_ready_health_check())
    monkeypatch.setattr(
        mlcore_client,
        "predict",
        lambda metadata: {
            "trending_probability": 0.71,
            "predicted_label": "trending",
            "predicted_label_display": "Trending",
            "confidence": 0.05,
            "confidence_band": "low",
            "model_version": "rf_v3",
            "top_features": ["genre=Thriller"],
            "grounded": True,
            "reason": None,
            "errors": [],
            "unknown_fields": [],
        },
    )

    response = client.post("/predict", json=_PREDICT_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["grounded"] is True
    assert body["trending_probability"] == 0.71
    assert body["predicted_label"] == "trending"


def test_predict_not_attempted_when_service_not_ready(monkeypatch):
    calls: list[dict] = []
    monkeypatch.setattr(
        mlcore_client,
        "health_check",
        lambda: {
            "status": "no_model",
            "model_loaded": False,
            "model_version": None,
            "metrics_ok": False,
            "roc_auc": None,
            "detail": "not ready",
        },
    )
    monkeypatch.setattr(mlcore_client, "predict", lambda metadata: calls.append(metadata) or {})

    response = client.post("/predict", json=_PREDICT_PAYLOAD)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "MODEL_NOT_READY"
    assert calls == []  # mlcore.predict() must never have been called
