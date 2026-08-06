"""The one error envelope shape every 4xx/5xx response uses.

Does NOT define per-endpoint error payloads — routes never construct this
directly, they raise an `AppError` subclass (core/errors.py) and the
registered exception handler builds the envelope.
"""
from __future__ import annotations

from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str
    detail: str | None = None


class ErrorEnvelope(BaseModel):
    error: ErrorBody
