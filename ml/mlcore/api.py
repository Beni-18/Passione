"""The ONLY module the backend imports (plan §1, §13).

    from mlcore.api import (
        health_check, load_model, get_model_metadata,
        predict, predict_batch, train_model,
    )

Signatures were frozen at M0 (T+35). This is the real implementation as of
M4 — behaviour changed, no shape changed. Thin re-export only: no logic
worth debugging lives in this file itself.
"""
from __future__ import annotations

from typing import Callable

from mlcore.predict import (
    get_model_metadata as _get_model_metadata,
)
from mlcore.predict import (
    health_check as _health_check,
)
from mlcore.predict import (
    load_model as _load_model,
)
from mlcore.predict import (
    predict as _predict,
)
from mlcore.predict import (
    predict_batch as _predict_batch,
)
from mlcore.train import train as _train


def health_check() -> dict:
    """Never raises. Backend maps status -> HTTP for GET /health."""
    return _health_check()


def load_model(version: str | None = None) -> dict:
    """Idempotent; caches in a module global. None -> version in latest.json.
    Call once at FastAPI startup, and again after training completes."""
    return _load_model(version)


def get_model_metadata() -> dict:
    """Everything the UI wants to display about the model itself."""
    return _get_model_metadata()


def predict(metadata: dict) -> dict:
    """THE function. NEVER raises — bad input returns grounded=false."""
    return _predict(metadata)


def predict_batch(items: list[dict]) -> list[dict]:
    """Same contract, per item. Errors are per-item, never global."""
    return _predict_batch(items)


def train_model(
    csv_path: str | None = None,
    progress_cb: Callable | None = None,
    seed: int = 42,
    algo: str = "logreg",
) -> dict:
    """Backend runs this in a BackgroundTask and stores the return value for /status.
    Raises ONLY on an unreadable/absent csv_path. Empty or header-only CSV
    returns status="failed" with rows_received=0 and a clear detail string."""
    return _train(csv_path=csv_path, progress_cb=progress_cb, seed=seed, algo=algo)
