#!/usr/bin/env python3
"""The 10-mark reproducibility gate (plan §10, handout Part 5 — no partial
credit). Runs train() twice against the same CSV and seed, in an isolated
artifacts dir, and asserts every evaluation metric matches exactly (floating
point) between the two runs.

Two full training runs never land in the same version directory (train.py
never overwrites — plan §11), and `trained_at` legitimately differs between
runs (real wall-clock time). So this compares the METRICS themselves, not a
raw byte-diff of the whole metrics.json file, which is what the handout's own
"two clean training runs... must produce the same evaluation metrics" actually
requires.

Usage: python3 ml/scripts/check_reproducibility.py
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ML_ROOT = Path(__file__).resolve().parents[1]
_isolated_dir = tempfile.mkdtemp(prefix="mlcore_repro_")
os.environ["ML_ARTIFACTS_DIR"] = _isolated_dir
sys.path.insert(0, str(ML_ROOT))

# Fields that legitimately differ between two identical runs (wall-clock time,
# the auto-incrementing version name) — excluded from the equality check.
_NON_DETERMINISTIC_KEYS = {"model_version", "trained_at"}


def main() -> int:
    from mlcore.train import train

    print("Run 1...")
    r1 = train(algo="logreg")
    print(f"  -> {r1['model_version']}, ROC-AUC={r1['metrics']['roc_auc']}")

    print("Run 2...")
    r2 = train(algo="logreg")
    print(f"  -> {r2['model_version']}, ROC-AUC={r2['metrics']['roc_auc']}")

    m1 = {k: v for k, v in r1["metrics"].items() if k not in _NON_DETERMINISTIC_KEYS}
    m2 = {k: v for k, v in r2["metrics"].items() if k not in _NON_DETERMINISTIC_KEYS}

    mismatches = [k for k in m1 if m1[k] != m2[k]]

    split1 = json.loads((Path(r1["artifacts_dir"]) / "split.json").read_text())
    split2 = json.loads((Path(r2["artifacts_dir"]) / "split.json").read_text())
    split_mismatches = [
        k for k in ("train_ids_sha256", "test_ids_sha256", "source_file_sha256")
        if split1[k] != split2[k]
    ]

    shutil.rmtree(_isolated_dir, ignore_errors=True)

    if not mismatches and not split_mismatches:
        print("\nPASS: metrics and split fingerprints are identical across both runs.")
        return 0

    print("\nFAIL: reproducibility gate did not pass.")
    for k in mismatches:
        print(f"  metrics['{k}']: run1={m1[k]!r}  run2={m2[k]!r}")
    for k in split_mismatches:
        print(f"  split['{k}']: run1={split1[k]!r}  run2={split2[k]!r}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
