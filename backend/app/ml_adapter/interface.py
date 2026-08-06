"""Protocols that define the ONLY shape backend code is allowed to assume
about a model bundle.

Every other backend module — services, routes — must depend on these
Protocols, never on sklearn, joblib, or ml/ directly. That is what makes
swapping stub.py for joblib_loader.py a one-file change. Does NOT implement
anything; see stub.py for the always-ungrounded implementation and
joblib_loader.py for the real one.
"""
from __future__ import annotations

from typing import Any, Protocol

import pandas as pd


class FeaturePipeline(Protocol):
    """The fitted sklearn pipeline half of a model bundle."""

    def transform(self, X: pd.DataFrame) -> Any:
        ...


class TrendModel(Protocol):
    """The fitted classifier half of a model bundle."""

    def predict_proba(self, X: Any) -> Any:
        """Returns [[p_not_trending, p_trending], ...] per docs/INTEGRATION.md."""
        ...


class BundleMeta(Protocol):
    model_version: str
    feature_names: list[str]
    known_categories: dict[str, list[str]]
    encoder_version: str
    random_seed: int
    trained_at: str


class LoadedBundle(Protocol):
    """What model_registry hands to prediction_service after a successful load."""

    pipeline: FeaturePipeline
    model: TrendModel
    meta: BundleMeta
