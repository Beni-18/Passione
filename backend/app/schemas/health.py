"""Response shape for GET /health.

`status` is computed by the route from model_registry.is_ready, not stored
here — this file only defines the shape, never the readiness logic.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    model_loaded: bool
    model_version: str | None
    enrichment_api_connected: bool
