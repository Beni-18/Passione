"""Choose settings for the non-linear models using training rows only.

    .venv/bin/python tune.py

For each candidate, the seed-0 training rows are split again (two inner 80/20 splits) and the model is scored on
the inner validation rows. The test rows are never touched, so the final test comparison in study.py stays fair.
The winners are written to results/tuned.json, which study.py reads.
"""

import itertools
import json
import time

import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

from common import RESULTS, dense_blocks, labels, load, split
from models import boosting, fusion

GRIDS = {
    "boosting": {"dims": [32, 64, 128], "learning_rate": [0.03, 0.1], "max_leaf_nodes": [15, 31]},
    "fusion": {"dims": [64, 256, None], "hidden": [128, 256], "lr": [1e-3, 3e-4], "p_drop": [0.3, 0.5]},
}
FEATURES = ["words", "title", "cover", "video"]
INNER_SEEDS = [11, 12]


def main() -> None:
    df, emb = load()
    y = labels(df)["raw"]
    outer_tr, _ = split(y, 0)  # the test rows of seed 0 are set aside and never used here
    results = {}
    for model, grid in GRIDS.items():
        fn = boosting if model == "boosting" else fusion
        scored = []
        for values in itertools.product(*grid.values()):
            params = dict(zip(grid, values))
            dims = params.pop("dims")
            aucs, t0 = [], time.time()
            for s in INNER_SEEDS:
                fit, val = train_test_split(outer_tr, test_size=0.2, stratify=y[outer_tr], random_state=s)
                blocks = dense_blocks(FEATURES, df, emb, fit, val, dims)
                aucs.append(roc_auc_score(y[val], fn(blocks, y[fit], s, **params)))
            scored.append({"dims": dims, **params, "val_roc_auc": float(np.mean(aucs))})
            print(f"{model:9} dims={dims} {params}  val ROC-AUC {np.mean(aucs):.4f}  ({time.time() - t0:.0f}s)", flush=True)
        scored.sort(key=lambda r: -r["val_roc_auc"])
        results[model] = {"best": scored[0], "all": scored}
        print(f"BEST {model}: {scored[0]}", flush=True)
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "tuned.json").write_text(json.dumps(results, indent=1))


if __name__ == "__main__":
    main()
