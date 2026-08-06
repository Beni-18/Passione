"""The real loader — the single file that changes when the ML model lands.

Reads models/model_v{N}.joblib (a dict with "pipeline", "model", "meta" keys)
per docs/INTEGRATION.md's Seam 1 and returns something satisfying
interface.LoadedBundle. Does NOT decide which version is active or check the
MIN_ROC_AUC bar — that's model_registry.py. Does NOT engineer any features —
the pipeline inside the bundle does all of that.

Not wired into model_registry yet; phase 1 skeleton uses ml_adapter/stub.py
exclusively. This file exists as scaffolding per CLAUDE.md section 3 and
will be implemented against a real .joblib artifact in a later phase.
"""
from __future__ import annotations

import joblib


def load_bundle(path: str):
    """Loads and returns the raw dict written by joblib.dump() at `path`.

    Raises whatever joblib/pickle raises on a corrupt or missing file —
    callers (model_registry) are responsible for catching that and falling
    back to the previously loaded model rather than crashing the service.
    """
    return joblib.load(path)
