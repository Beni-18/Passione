"""Response shape for POST /train.

Does NOT define the background job's internal state machine — that's
job_manager.py's JobRecord. POST /train has no JSON body: it's multipart
only (file + a random_seed form field), read directly as route parameters
in routes/train.py — there is deliberately no request schema class here.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class TrainAcceptedResponse(BaseModel):
    job_id: str
    rows_received: int
    status: Literal["queued"]
