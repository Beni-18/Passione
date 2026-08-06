"""Request/response shapes for POST /train.

Does NOT define the background job's internal state machine — that's
job_manager.py's JobRecord. This is only the wire shape of the 202 response
and the JSON-body request variant (the multipart file variant has no body
schema; FastAPI reads it as an UploadFile in the route).
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class TrainRequest(BaseModel):
    csv_path: str
    random_seed: int = 42


class TrainAcceptedResponse(BaseModel):
    job_id: str
    rows_received: int
    status: Literal["queued"]
