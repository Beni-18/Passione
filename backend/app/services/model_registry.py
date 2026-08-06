"""Discovers, loads, versions, and activates model artifacts.

Owns the answer to "is a model ready to serve predictions?" Discovers
models/model_v*.joblib, picks the highest version (or the one explicitly
activated via POST /models/activate), validates meta, and checks roc_auc
against settings.min_roc_auc to set is_ready. Keeps the previously loaded
model live if a new artifact fails to load — never leaves the service with
nothing loaded because of a bad retrain.

In phase 1 (this skeleton) no real .joblib files exist yet, so this always
resolves to the stub adapter: is_ready is always False, active_version is
always None. joblib_loader.py is not called from here until a later phase.
"""
from __future__ import annotations

from app.ml_adapter.stub import StubBundle


class ModelRegistry:
    def __init__(self) -> None:
        self._active_bundle: StubBundle = StubBundle()
        self._active_version: str | None = None
        self._available_versions: list[str] = []

    @property
    def is_ready(self) -> bool:
        """True only when a real model is loaded AND cleared MIN_ROC_AUC.

        Always False in phase 1 since only the stub bundle exists.
        """
        return False

    @property
    def active_version(self) -> str | None:
        return self._active_version

    @property
    def available_versions(self) -> list[str]:
        return self._available_versions

    @property
    def active_bundle(self) -> StubBundle:
        return self._active_bundle

    def activate(self, model_version: str) -> str:
        """Switches the active model to `model_version` without retraining.

        Phase 1: no real artifacts exist, so this always raises — there is
        nothing to activate yet. Real discovery/activation logic lands with
        joblib_loader.py in a later phase.
        """
        raise NotImplementedError(
            f"No model artifacts are available to activate (requested {model_version!r})."
        )


# Process-wide singleton, mirroring job_manager's lifecycle.
model_registry = ModelRegistry()
