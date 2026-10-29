"""Run every (label, model, feature set, seed) combination and save the test-set predictions.

    .venv/bin/python study.py            # everything (resumes: finished runs are skipped)
    .venv/bin/python study.py --quick    # one seed, to check the pipeline end to end

Predictions land in results/preds/ as one .npy per run; analyze.py turns them into tables and figures.
"""

import argparse
import json
import time

import numpy as np
from sklearn.metrics import roc_auc_score

from common import RESULTS, SEEDS, dense_blocks, labels, load, sparse_blocks, split
from models import MODELS

FEATURE_SETS = {
    "words": ["words"],
    "words+title": ["words", "title"],
    "words+title+cover": ["words", "title", "cover"],
    "all": ["words", "title", "cover", "video"],
    "cover": ["cover"],
    "video": ["video"],
    # Phase 2: our own SigLIP 2 cover embedding in place of the authors' CLIP RN50
    "cover_sl2": ["cover_sl2"],
    "words+title+cover_sl2": ["words", "title", "cover_sl2"],
    "words+title+cover_sl2+video": ["words", "title", "cover_sl2", "video"],
}
# The age-adjusted label is a robustness check, so it gets the incremental sets only.
LABEL_SETS = {"raw": list(FEATURE_SETS),
              "age_adjusted": ["words", "words+title", "words+title+cover", "all", "words+title+cover_sl2"]}


def settings() -> dict[str, tuple[int | None, dict]]:
    """Block width and model settings per model: tuned on training rows by tune.py, else the defaults."""
    out = {"linear": (None, {}), "boosting": (64, {}), "fusion": (64, {})}
    path = RESULTS / "tuned.json"
    if path.exists():
        for model, res in json.loads(path.read_text()).items():
            best = {k: v for k, v in res["best"].items() if k != "val_roc_auc"}
            out[model] = (best.pop("dims"), best)
    return out


def run(quick: bool) -> None:
    df, emb = load()
    ys = labels(df)
    out = RESULTS / "preds"
    out.mkdir(parents=True, exist_ok=True)
    seeds = SEEDS[:1] if quick else SEEDS
    conf = settings()
    print("settings:", conf, flush=True)
    for label, sets in LABEL_SETS.items():
        sets = [fs for fs in sets if all(n == "words" or n in emb for n in FEATURE_SETS[fs])]  # skip missing inputs
        y = ys[label]
        for seed in seeds:
            tr, te = split(y, seed)
            np.save(out / f"{label}__split__s{seed}.npy", te)
            np.save(out / f"{label}__y__s{seed}.npy", y[te])
            for fs in sets:
                names = FEATURE_SETS[fs]
                cache = {}
                for model, fn in MODELS.items():
                    path = out / f"{label}__{model}__{fs}__s{seed}.npy"
                    if path.exists():
                        continue
                    dims, params = conf[model]
                    kind = "sparse" if model == "linear" else f"dense{dims}"
                    if kind not in cache:
                        cache[kind] = (sparse_blocks(names, df, emb, tr, te) if kind == "sparse"
                                       else dense_blocks(names, df, emb, tr, te, dims))
                    t0 = time.time()
                    p = fn(cache[kind], y[tr], seed, **params)
                    np.save(path, p.astype(np.float32))
                    print(f"{label:13} s{seed} {model:9} {fs:18} ROC-AUC {roc_auc_score(y[te], p):.3f}  ({time.time() - t0:.0f}s)",
                          flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    run(ap.parse_args().quick)
