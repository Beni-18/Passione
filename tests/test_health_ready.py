"""GET /health's "ok" vs "degraded" boundary against MIN_ROC_AUC.

The real dummy mlcore never reports a loaded model, so this monkeypatches
mlcore_client.health_check directly (same pattern as
tests/test_grounding_ownership.py) to exercise the "ok" path and to confirm
the threshold is a real `>=` check, not off-by-one in either direction.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

import app.ml_adapter.mlcore_client as mlcore_client
from app.core.config import settings
from app.main import app

client = TestClient(app)


def _health_check_with_roc_auc(roc_auc: float):
    return lambda: {
        "status": "ready",
        "model_loaded": True,
        "model_version": "rf_v3",
        "metrics_ok": True,
        "roc_auc": roc_auc,
        "detail": None,
    }


def test_health_ok_when_roc_auc_above_threshold(monkeypatch):
    monkeypatch.setattr(
        mlcore_client, "health_check", _health_check_with_roc_auc(settings.min_roc_auc + 0.05)
    )

    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True
    assert body["model_version"] == "rf_v3"


def test_health_ok_when_roc_auc_exactly_at_threshold(monkeypatch):
    # >= , not > — the boundary value itself must pass.
    monkeypatch.setattr(
        mlcore_client, "health_check", _health_check_with_roc_auc(settings.min_roc_auc)
    )

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_degraded_when_roc_auc_just_below_threshold(monkeypatch):
    monkeypatch.setattr(
        mlcore_client, "health_check", _health_check_with_roc_auc(settings.min_roc_auc - 0.01)
    )

    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    # model_loaded is reported independently of the roc_auc gate — mlcore
    # says a model IS loaded, just not one that clears the bar.
    assert body["model_loaded"] is True


def test_health_degraded_when_model_not_loaded_even_with_high_roc_auc(monkeypatch):
    monkeypatch.setattr(
        mlcore_client,
        "health_check",
        lambda: {
            "status": "no_model",
            "model_loaded": False,
            "model_version": None,
            "metrics_ok": False,
            "roc_auc": 0.99,
            "detail": None,
        },
    )

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
