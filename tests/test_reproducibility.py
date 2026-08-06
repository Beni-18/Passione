"""Two runs, same seed, identical metrics — CLAUDE.md hard requirement 3,
zero partial credit.

Phase M0: mlcore.train_model is still the dummy from ml/mlcore/api.py, so
this asserts determinism of the frozen-interface call itself (trivial at
this stage since the dummy ignores its inputs). Once the ML owner's real
training lands (M3/M4) inside mlcore, this must assert the same thing against
real fitted output — two calls to mlcore.api.train_model on the same CSV and
seed must return byte-identical metrics dicts. The assertion shape below
does not change; only mlcore's internals do (docs/INTEGRATION.md Seam 1).
"""
from __future__ import annotations

from mlcore.api import train_model


def test_train_model_is_deterministic_given_same_input():
    result_a = train_model(csv_path="data/samples/clean_50.csv", seed=42)
    result_b = train_model(csv_path="data/samples/clean_50.csv", seed=42)

    assert result_a == result_b
