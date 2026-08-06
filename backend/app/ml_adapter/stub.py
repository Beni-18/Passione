"""The always-ungrounded adapter wired in until a real model artifact lands.

Used whenever model_registry finds no valid models/model_v*.joblib +
metrics_v*.json pair on disk. It never returns a probability and never
claims a model is loaded — /health stays "degraded" and /predict stays
grounded: false for as long as this is the active adapter. Does NOT read
any file from disk; it is pure in-memory placeholder state.
"""
from __future__ import annotations


class StubBundle:
    """Sentinel bundle: satisfies model_registry's "is something loaded?"
    check by being present, but carries no usable pipeline or model.
    """

    model_version: str | None = None
    is_stub: bool = True

    def predict(self, *_args, **_kwargs) -> None:
        raise NotImplementedError(
            "StubBundle cannot predict — no model has been trained yet. "
            "Callers must check model_registry.is_ready before predicting."
        )
