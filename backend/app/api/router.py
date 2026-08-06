"""The single place all routers are included.

main.py imports only `api_router` from here — no route module is ever
attached to the FastAPI app directly, so the full surface is always visible
in one file, in the order printed in the API surface report.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import health, metrics, models, predict, status, train

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(train.router, tags=["train"])
api_router.include_router(status.router, tags=["status"])
api_router.include_router(predict.router, tags=["predict"])
api_router.include_router(metrics.router, tags=["metrics"])
api_router.include_router(models.router, tags=["models"])
