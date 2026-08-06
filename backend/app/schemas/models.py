"""Request/response shapes for GET /models and POST /models/activate.

Not enumerated as a separate file under CLAUDE.md section 3's schemas/ list,
but section 6 requires every response to be a schema class — added here
rather than inlining dicts in routes/models.py.
"""
from __future__ import annotations

from pydantic import BaseModel


class ModelListResponse(BaseModel):
    active: str | None
    available: list[str]


class ActivateModelRequest(BaseModel):
    model_version: str


class ActiveModelResponse(BaseModel):
    active: str
