"""Response shape for GET /metrics, mirrors metrics_v{N}.json exactly.

Field set is fixed by docs/INTEGRATION.md's Seam 1 contract — do not add
fields here without updating that doc and the ML owner, since this is the
same shape the ML owner writes to disk and the backend echoes verbatim.
"""
from __future__ import annotations

from pydantic import BaseModel


class SplitCounts(BaseModel):
    train: int
    val: int
    test: int


class MetricsResponse(BaseModel):
    model_version: str
    precision: float
    recall: float
    f1: float
    roc_auc: float
    accuracy: float
    positive_rate: float
    random_seed: int
    split: SplitCounts
    trained_at: str
