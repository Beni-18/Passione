"""Passioné v2: does the video itself help predict which micro-videos trend?

Data: MicroLens-100k (Westlake University; Ni et al., "A Content-Driven Micro-Video Recommendation Dataset at
Scale"), 19,738 real micro-videos with view counts. Run `python fetch_microlens.py` first.

Label: trending = top 25% by views (the Passioné v1 rule). Likes are never used as a feature: they are a
consequence of views, so using them would leak the answer.

Feature sets, each added on top of the previous one:
  1. title words      : TF-IDF over the title (the metadata-only approach of v1)
  2. + title meaning  : BGE-M3 sentence embedding of the title
  3. + cover image    : CLIP RN50 embedding of the cover
  4. + video content  : VideoMAE embedding of the clip (a video transformer over sampled frames)
  and, for contrast, video content alone.
The embeddings are the dataset authors' pre-extracted features; this script trains and evaluates the models.

Evaluation: logistic regression (class-weighted, C chosen by 3-fold CV on the training split), scored on a
held-out 20% split, repeated over 5 random splits; ROC-AUC and F1 reported as mean ± std.

Usage: uv run --no-project --with numpy,pandas,scikit-learn,scipy python passione_v2.py
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
TOP_SHARE = 0.25
SEEDS = [0, 1, 2, 3, 4]


def load() -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    views = pd.read_csv(DATA / "MicroLens-100k_likes_and_views.txt", sep="\t", header=None, names=["item", "likes", "views"])
    # "<id>, <title>" per line; titles can contain commas, so split on the first one only
    lines = (DATA / "MicroLens-100k_title_en.csv").read_text(encoding="utf-8").splitlines()
    titles = pd.DataFrame(
        [(int(i), t.strip()) for i, t in (line.split(",", 1) for line in lines)], columns=["item", "title"]
    )
    df = views.merge(titles, on="item", how="left").sort_values("item").reset_index(drop=True)
    df["title"] = df["title"].fillna("")
    assert (df["item"].values == np.arange(1, len(df) + 1)).all(), "rows must be items 1..N in order"
    emb = {  # row i of each matrix is item i+1 (checked against the authors' JSON)
        "title": np.load(DATA / "MicroLens-100k_title_en_text_features_BgeM3.npy"),
        "cover": np.load(DATA / "MicroLens-100k_image_features_CLIPRN50.npy"),
        "video": np.load(DATA / "MicroLens-100k_video_features_VideoMAE.npy"),
    }
    assert all(len(m) == len(df) for m in emb.values())
    return df, emb


def evaluate(blocks: list[str], df: pd.DataFrame, emb: dict, y: np.ndarray, seed: int) -> tuple[float, float]:
    tr, te = train_test_split(np.arange(len(df)), test_size=0.2, stratify=y, random_state=seed)
    parts_tr, parts_te = [], []
    if "words" in blocks:
        tfidf = TfidfVectorizer(max_features=20000, ngram_range=(1, 2), min_df=2, sublinear_tf=True)
        parts_tr.append(tfidf.fit_transform(df["title"].iloc[tr]))
        parts_te.append(tfidf.transform(df["title"].iloc[te]))
        length = df["title"].str.split().str.len().to_numpy(dtype=float)[:, None] / 20
        parts_tr.append(csr_matrix(length[tr]))
        parts_te.append(csr_matrix(length[te]))
    for name in ("title", "cover", "video"):
        if name in blocks:
            scaler = StandardScaler().fit(emb[name][tr])
            parts_tr.append(csr_matrix(scaler.transform(emb[name][tr]) / np.sqrt(emb[name].shape[1])))
            parts_te.append(csr_matrix(scaler.transform(emb[name][te]) / np.sqrt(emb[name].shape[1])))
    x_tr, x_te = hstack(parts_tr).tocsr(), hstack(parts_te).tocsr()
    search = GridSearchCV(
        LogisticRegression(max_iter=3000, class_weight="balanced"),
        {"C": [0.1, 0.3, 1.0, 3.0]},
        scoring="roc_auc",
        cv=3,
        n_jobs=-1,
    ).fit(x_tr, y[tr])
    p = search.predict_proba(x_te)[:, 1]
    return roc_auc_score(y[te], p), f1_score(y[te], p >= 0.5)


def main() -> int:
    df, emb = load()
    y = (df["views"] >= df["views"].quantile(1 - TOP_SHARE)).astype(int).to_numpy()
    print(f"{len(df)} videos, positive rate {y.mean():.3f}, view threshold {df['views'].quantile(1 - TOP_SHARE):,.0f}")
    configs = {
        "1. title words (TF-IDF, v1-style metadata)": ["words"],
        "2. + title meaning (BGE-M3)": ["words", "title"],
        "3. + cover image (CLIP)": ["words", "title", "cover"],
        "4. + video content (VideoMAE)": ["words", "title", "cover", "video"],
        "video content alone (VideoMAE)": ["video"],
    }
    rows = []
    for name, blocks in configs.items():
        scores = np.array([evaluate(blocks, df, emb, y, s) for s in SEEDS])
        auc, f1 = scores.mean(0), scores.std(0)
        rows.append({"model": name, "roc_auc": round(auc[0], 3), "roc_auc_std": round(f1[0], 3),
                     "f1": round(auc[1], 3), "f1_std": round(f1[1], 3)})
        print(f"  {name:<46} ROC-AUC {auc[0]:.3f} ± {f1[0]:.3f}   F1 {auc[1]:.3f} ± {f1[1]:.3f}")
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "results.csv", index=False)
    (HERE / "results.json").write_text(json.dumps({"n_videos": len(df), "test_share": 0.2, "seeds": SEEDS,
                                                   "positive_rate": float(y.mean()), "results": rows}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
