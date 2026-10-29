"""Turn the saved predictions into tables, paired comparisons, calibration and error analysis.

    .venv/bin/python analyze.py

Writes results/phase1.json, results/phase1.md and figures/*.png.

Paired comparisons: every model and feature set is scored on the same test rows for a given seed, so the
difference in ROC-AUC between two runs is computed per seed and then resampled together (paired bootstrap, 2,000
resamples per seed, averaged over seeds). A 95% interval that excludes zero means the gain is not test-set noise.

Calibration: training used balanced class weights, which pushes scores towards 0.5 on purpose, so raw scores are
not probabilities. Recalibration is estimated by cross-fitting on the test rows (isotonic regression fit on one
half, scored on the other, then swapped), so no row is scored by a calibrator that saw it.
"""

import json
from itertools import product

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss, f1_score, roc_auc_score

from common import FIGURES, RESULTS, SEEDS, labels, load
from study import FEATURE_SETS, LABEL_SETS
from models import MODELS

PREDS = RESULTS / "preds"
N_BOOT = 2000
STEPS = [  # (question, from feature set, to feature set)
    ("title meaning (BGE-M3) on top of title words", "words", "words+title"),
    ("cover image (CLIP) on top of the title", "words+title", "words+title+cover"),
    ("video content (VideoMAE) on top of title and cover", "words+title+cover", "all"),
    ("SigLIP 2 cover in place of CLIP RN50 (with the title)", "words+title+cover", "words+title+cover_sl2"),
    ("SigLIP 2 cover in place of CLIP RN50 (cover alone)", "cover", "cover_sl2"),
    ("video content on top of title and SigLIP 2 cover", "words+title+cover_sl2", "words+title+cover_sl2+video"),
]
FS_LABELS = {"words": "title words", "words+title": "+ title meaning", "words+title+cover": "+ cover image",
             "all": "+ video content", "cover": "cover only", "video": "video only",
             "cover_sl2": "SigLIP 2 cover only", "words+title+cover_sl2": "title + SigLIP 2 cover",
             "words+title+cover_sl2+video": "title + SigLIP 2 cover + video"}


def load_runs() -> dict:
    runs = {}
    for label, model, fs, seed in product(LABEL_SETS, MODELS, FEATURE_SETS, SEEDS):
        path = PREDS / f"{label}__{model}__{fs}__s{seed}.npy"
        if path.exists():
            runs[(label, model, fs, seed)] = np.load(path)
    return runs


def split_of(label: str, seed: int) -> tuple[np.ndarray, np.ndarray]:
    return np.load(PREDS / f"{label}__split__s{seed}.npy"), np.load(PREDS / f"{label}__y__s{seed}.npy")


def boot_auc(y: np.ndarray, p: np.ndarray, counts: np.ndarray) -> np.ndarray:
    """Exact ROC-AUC for many bootstrap resamples at once.

    `counts[b, i]` is how often row i was drawn in resample b. Rows are sorted by score once; tied scores are
    grouped, and a positive scores 1 for every lower-scored negative and 0.5 for every tied one (the Mann-Whitney
    definition, which is what roc_auc_score computes).
    """
    order = np.argsort(p, kind="stable")
    ps, ys, w = p[order], y[order], counts[:, order]
    starts = np.r_[0, np.flatnonzero(np.diff(ps)) + 1]  # first row of each group of tied scores
    pos = np.add.reduceat(w * ys, starts, axis=1)
    neg = np.add.reduceat(w * (1 - ys), starts, axis=1)
    neg_below = np.cumsum(neg, axis=1) - neg
    return (pos * (neg_below + 0.5 * neg)).sum(axis=1) / (pos.sum(axis=1) * neg.sum(axis=1))


def paired_delta(runs, label, model_a, fs_a, model_b, fs_b, seeds) -> dict | None:
    """Mean ROC-AUC gain of b over a, with a 95% paired-bootstrap interval pooled over seeds."""
    rng = np.random.default_rng(0)
    deltas, boots = [], np.zeros(N_BOOT)
    used = [s for s in seeds if (label, model_a, fs_a, s) in runs and (label, model_b, fs_b, s) in runs]
    if not used:
        return None
    for s in used:
        _, y = split_of(label, s)
        pa, pb = runs[(label, model_a, fs_a, s)], runs[(label, model_b, fs_b, s)]
        deltas.append(roc_auc_score(y, pb) - roc_auc_score(y, pa))
        counts = rng.multinomial(len(y), np.full(len(y), 1 / len(y)), size=N_BOOT)  # same resamples for a and b
        boots += boot_auc(y, pb, counts) - boot_auc(y, pa, counts)
    boots /= len(used)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"delta": float(np.mean(deltas)), "ci95": [float(lo), float(hi)], "seeds": len(used),
            "significant": bool(lo > 0 or hi < 0)}


def ece(y: np.ndarray, p: np.ndarray, bins: int = 15) -> float:
    edges = np.linspace(0, 1, bins + 1)
    which = np.clip(np.digitize(p, edges) - 1, 0, bins - 1)
    return float(sum(abs(p[which == b].mean() - y[which == b].mean()) * (which == b).mean()
                     for b in range(bins) if (which == b).any()))


def crossfit_isotonic(y: np.ndarray, p: np.ndarray, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    half = rng.permutation(len(y)) < len(y) // 2
    out = np.empty_like(p)
    for fit, score in ((half, ~half), (~half, half)):
        out[score] = IsotonicRegression(out_of_bounds="clip").fit(p[fit], y[fit]).predict(p[score])
    return out


def main() -> None:
    FIGURES.mkdir(exist_ok=True)
    df, _ = load()
    ys = labels(df)
    runs = load_runs()
    report: dict = {"n_videos": int(len(df)), "seeds": SEEDS, "positive_rate": float(ys["raw"].mean())}

    # 1. Is the label mostly about age?
    cohort = pd.qcut(df["age_days"], 5, labels=["newest", "2nd", "3rd", "4th", "oldest"])
    by_age = df.assign(trending=ys["raw"], cohort=cohort).groupby("cohort", observed=True).agg(
        trending_rate=("trending", "mean"), median_age_days=("age_days", "median"), median_views=("views", "median"))
    report["age_check"] = {
        "age_alone_roc_auc": float(roc_auc_score(ys["raw"], df["age_days"])),
        "by_age_fifth": by_age.round(3).reset_index().to_dict("records"),
        "labels_agree": float((ys["raw"] == ys["age_adjusted"]).mean()),
    }
    fig, ax = plt.subplots(figsize=(6, 3.2))
    ax.bar(by_age.index.astype(str), by_age["trending_rate"] * 100, color="#4c78a8")
    ax.axhline(25, ls="--", c="grey", lw=1)
    ax.set_ylabel("% labelled trending")
    ax.set_xlabel("videos grouped by age (fifths)")
    ax.set_title("Newer videos had less time to collect views")
    fig.tight_layout()
    fig.savefig(FIGURES / "age_check.png", dpi=150)
    plt.close(fig)

    # 2. Scores per label, model and feature set (mean ± std over seeds)
    rows = []
    for (label, model, fs), group in pd.Series(runs).groupby(level=[0, 1, 2]):
        aucs, f1s, briers = [], [], []
        for (_, _, _, seed), p in group.items():
            _, y = split_of(label, seed)
            aucs.append(roc_auc_score(y, p))
            f1s.append(f1_score(y, p >= 0.5))
            briers.append(brier_score_loss(y, p))
        rows.append({"label": label, "model": model, "features": fs, "seeds": len(aucs),
                     "roc_auc": np.mean(aucs), "roc_auc_std": np.std(aucs), "f1": np.mean(f1s), "f1_std": np.std(f1s),
                     "brier": np.mean(briers)})
    table = pd.DataFrame(rows)
    report["scores"] = table.round(4).to_dict("records")

    # 3. Paired comparisons: does each modality help, and does a non-linear model help?
    comps = []
    for label in LABEL_SETS:
        for model in MODELS:
            for question, a, b in STEPS:
                r = paired_delta(runs, label, model, a, model, b, SEEDS)
                if r:
                    comps.append({"label": label, "model": model, "question": question, **r})
        for model in ("boosting", "fusion"):
            r = paired_delta(runs, label, "linear", "all", model, "all", SEEDS)
            if r:
                comps.append({"label": label, "model": f"{model} vs linear", "question": "non-linear fusion, all inputs", **r})
    report["comparisons"] = comps

    # 4. Ablation figure (raw label)
    raw = table[table.label == "raw"]
    order = [fs for fs in FEATURE_SETS if fs in set(raw.features)]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    width = 0.27
    for i, model in enumerate(MODELS):
        sub = raw[raw.model == model].set_index("features").reindex(order)
        ax.bar(np.arange(len(order)) + (i - 1) * width, sub["roc_auc"], width, yerr=sub["roc_auc_std"], capsize=2,
               label=model)
    ax.set_xticks(np.arange(len(order)), [FS_LABELS[f] for f in order], rotation=15, ha="right")
    ax.set_ylim(0.5, max(0.75, raw["roc_auc"].max() + 0.02))
    ax.axhline(0.5, c="grey", lw=1)
    ax.set_ylabel("ROC-AUC (test, 5 seeds)")
    ax.set_title("What each input adds, per model")
    ax.legend(frameon=False, ncol=3, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIGURES / "ablation.png", dpi=150)
    plt.close(fig)

    # 5. Calibration and error analysis for the best raw-label run
    best = raw.sort_values("roc_auc", ascending=False).iloc[0]
    report["best"] = {"model": best.model, "features": best.features, "roc_auc": float(best.roc_auc)}
    ps, yy, items = [], [], []
    for seed in SEEDS:
        key = ("raw", best.model, best.features, seed)
        if key in runs:
            te, y = split_of("raw", seed)
            ps.append(runs[key]); yy.append(y); items.append(te)
    p, y, items = np.concatenate(ps), np.concatenate(yy), np.concatenate(items)
    p_cal = crossfit_isotonic(y, p)
    report["calibration"] = {
        "raw": {"ece": ece(y, p), "brier": float(brier_score_loss(y, p)), "mean_score": float(p.mean())},
        "isotonic_crossfit": {"ece": ece(y, p_cal), "brier": float(brier_score_loss(y, p_cal)),
                              "mean_score": float(p_cal.mean())},
        "base_rate": float(y.mean()),
    }
    fig, ax = plt.subplots(figsize=(4.2, 4.2))
    for name, q in (("as trained (balanced weights)", p), ("after isotonic calibration", p_cal)):
        edges = np.linspace(0, 1, 11)
        which = np.clip(np.digitize(q, edges) - 1, 0, 9)
        xs = [q[which == b].mean() for b in range(10) if (which == b).sum() > 30]
        ys_ = [y[which == b].mean() for b in range(10) if (which == b).sum() > 30]
        ax.plot(xs, ys_, marker="o", label=name)
    ax.plot([0, 1], [0, 1], ls="--", c="grey", lw=1)
    ax.set_xlabel("predicted probability")
    ax.set_ylabel("observed trending rate")
    ax.set_title("Calibration")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURES / "calibration.png", dpi=150)
    plt.close(fig)

    # A video can be in the test set under several seeds: average its scores so each video counts once.
    err = (pd.DataFrame({"row": items, "p": p, "y": y}).groupby("row").agg(p=("p", "mean"), y=("y", "first"))
           .join(df, on="row").reset_index(drop=True))
    from scipy.stats import spearmanr
    report["ranking"] = {
        "videos": int(len(err)),
        "spearman_score_vs_log_views": float(spearmanr(err["p"], np.log10(err["views"]))[0]),
    }
    err["title_words"] = err["title"].str.split().str.len()
    threshold = df["views"].quantile(0.75)
    report["cutoff_views"] = float(threshold)
    err["distance"] = np.log10(err["views"] / threshold)
    slices = {
        "age fifth": pd.qcut(err["age_days"], 5, labels=["newest", "2nd", "3rd", "4th", "oldest"]),
        "title length": pd.cut(err["title_words"], [-1, 3, 7, 12, 1000], labels=["0-3 words", "4-7", "8-12", "13+"]),
        "views vs cut-off": pd.cut(err["distance"], [-9, -0.5, -0.15, 0.15, 0.5, 9],
                                   labels=["far below", "below", "near the cut-off", "above", "far above"]),
    }
    report["slices"] = {}
    for name, groups in slices.items():
        out = []
        for g, part in err.groupby(groups, observed=True):
            auc = roc_auc_score(part.y, part.p) if part.y.nunique() == 2 else None
            acc = float(((part.p >= 0.5) == part.y).mean())
            out.append({"slice": str(g), "n": int(len(part)), "roc_auc": auc, "accuracy_at_0.5": acc,
                        "trending_rate": float(part.y.mean())})
        report["slices"][name] = out
    fp = err[(err.y == 0)].nlargest(8, "p")[["item", "title", "views", "p"]]
    fn = err[(err.y == 1)].nsmallest(8, "p")[["item", "title", "views", "p"]]
    report["confident_errors"] = {"false_positives": fp.round(3).to_dict("records"),
                                  "false_negatives": fn.round(3).to_dict("records")}

    (RESULTS / "phase1.json").write_text(json.dumps(report, indent=1, default=float))
    write_markdown(report, table)
    print((RESULTS / "phase1.md").read_text())


def write_markdown(report: dict, table: pd.DataFrame) -> None:
    pct = lambda x: f"{x * 100:.1f}%"
    lines = ["# Passioné v2, phase 1 results", "",
             f"{report['n_videos']:,} micro-videos, positive rate {pct(report['positive_rate'])}, "
             f"test share 20%, seeds {report['seeds']}.", ""]
    a = report["age_check"]
    lines += ["## Is the label mostly about age?", "",
              f"Age alone predicts the raw label at ROC-AUC {a['age_alone_roc_auc']:.3f}. "
              f"The raw and age-adjusted labels agree on {pct(a['labels_agree'])} of videos.", "",
              "| age fifth | trending rate | median age (days) | median views |", "|:--|--:|--:|--:|"]
    lines += [f"| {r['cohort']} | {pct(r['trending_rate'])} | {r['median_age_days']:.0f} | {r['median_views']:,.0f} |"
              for r in a["by_age_fifth"]]
    for label in LABEL_SETS:
        sub = table[table.label == label]
        if sub.empty:
            continue
        lines += ["", f"## ROC-AUC, {label.replace('_', '-')} label (mean ± std over seeds)", "",
                  "| features | " + " | ".join(MODELS) + " |", "|:--|" + "--:|" * len(MODELS)]
        for fs in FEATURE_SETS:
            cells = []
            for model in MODELS:
                r = sub[(sub.model == model) & (sub.features == fs)]
                cells.append(f"{r.roc_auc.iloc[0]:.3f} ± {r.roc_auc_std.iloc[0]:.3f}" if len(r) else "")
            if any(cells):
                lines.append(f"| {FS_LABELS[fs]} | " + " | ".join(cells) + " |")
    lines += ["", "## Paired comparisons (ROC-AUC gain, 95% paired bootstrap)", "",
              "| label | model | question | gain | 95% interval | real? |", "|:--|:--|:--|--:|:--|:--|"]
    for c in report["comparisons"]:
        lines.append(f"| {c['label']} | {c['model']} | {c['question']} | {c['delta']:+.3f} | "
                     f"[{c['ci95'][0]:+.3f}, {c['ci95'][1]:+.3f}] | {'yes' if c['significant'] else 'no'} |")
    rk = report["ranking"]
    lines += ["", "## Ranking, without a cut-off", "",
              f"Spearman correlation between the model's score and log views, over {rk['videos']:,} test videos "
              f"(each counted once): {rk['spearman_score_vs_log_views']:.3f}."]
    cal, best = report["calibration"], report["best"]
    lines += ["", f"## Calibration ({best['model']}, {FS_LABELS[best['features']]})", "",
              "| scores | ECE | Brier | mean score |", "|:--|--:|--:|--:|",
              f"| as trained | {cal['raw']['ece']:.3f} | {cal['raw']['brier']:.3f} | {cal['raw']['mean_score']:.3f} |",
              f"| isotonic (cross-fit) | {cal['isotonic_crossfit']['ece']:.3f} | {cal['isotonic_crossfit']['brier']:.3f} | "
              f"{cal['isotonic_crossfit']['mean_score']:.3f} |",
              f"| base rate | | | {cal['base_rate']:.3f} |"]
    lines += ["", "## Where it goes wrong", "",
              f"Cut-off for trending: {report['cutoff_views']:,.0f} views. \"Near the cut-off\" means within a factor "
              "of 1.4 either side.", ""]
    for name, rows in report["slices"].items():
        lines += [f"**{name}**", "", "| slice | n | ROC-AUC | accuracy at 0.5 | trending rate |", "|:--|--:|--:|--:|--:|"]
        lines += [f"| {r['slice']} | {r['n']:,} | {r['roc_auc']:.3f} | {pct(r['accuracy_at_0.5'])} | {pct(r['trending_rate'])} |"
                  if r["roc_auc"] is not None else
                  f"| {r['slice']} | {r['n']:,} | n/a | {pct(r['accuracy_at_0.5'])} | {pct(r['trending_rate'])} |"
                  for r in rows]
        lines.append("")
    lines += ["**Most confident mistakes** (score averaged over the seeds where the video was in the test set)", "",
              "| type | score | views | title |", "|:--|--:|--:|:--|"]
    for kind, rows in (("false positive", report["confident_errors"]["false_positives"]),
                       ("false negative", report["confident_errors"]["false_negatives"])):
        lines += [f"| {kind} | {r['p']:.2f} | {r['views']:,} | {r['title'][:70].replace('|', '/')} |" for r in rows[:5]]
    (RESULTS / "phase1.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
