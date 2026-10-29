"""Shared data loading, labels, splits and feature blocks for the Passioné v2 study.

Data: MicroLens-100k (Westlake University; Ni et al., "A Content-Driven Micro-Video Recommendation Dataset at
Scale"), 19,738 micro-videos with view counts. Run `python fetch_microlens.py` first.

Everything that learns from data (TF-IDF vocabulary, SVD, PCA, scalers) is fit on the training rows of a split
only, so no test information leaks into the features.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
RESULTS = HERE / "results"
FIGURES = HERE / "figures"
TOP_SHARE = 0.25
SEEDS = [0, 1, 2, 3, 4]
TEST_SHARE = 0.2
EMBEDDINGS = ("title", "cover", "cover_sl2", "video")
# title BGE-M3, cover CLIP RN50 and video VideoMAE are the dataset authors' features;
# cover_sl2 is our own SigLIP 2 embedding of the same covers (embed.py)


def load() -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    """One row per video (item ids 1..N in order) plus the three embedding matrices, row i = item i+1."""
    views = pd.read_csv(DATA / "MicroLens-100k_likes_and_views.txt", sep="\t", header=None, names=["item", "likes", "views"])
    # "<id>, <title>" per line; titles can contain commas, so split on the first one only
    lines = (DATA / "MicroLens-100k_title_en.csv").read_text(encoding="utf-8").splitlines()
    titles = pd.DataFrame([(int(i), t.strip()) for i, t in (line.split(",", 1) for line in lines)], columns=["item", "title"])
    df = views.merge(titles, on="item", how="left").sort_values("item").reset_index(drop=True)
    df["title"] = df["title"].fillna("")
    assert (df["item"].values == np.arange(1, len(df) + 1)).all(), "rows must be items 1..N in order"

    # Age proxy: the dataset has no upload time, so use the first logged interaction. It is a lower bound on age
    # (the log samples 100k users), good enough to test whether older videos simply had longer to collect views.
    pairs = pd.read_csv(DATA / "MicroLens-100k_pairs.csv")
    first = pairs.groupby("item").timestamp.min()
    df["age_days"] = (pairs.timestamp.max() - df["item"].map(first).to_numpy()) / 86_400_000

    emb = {
        "title": np.load(DATA / "MicroLens-100k_title_en_text_features_BgeM3.npy"),
        "cover": np.load(DATA / "MicroLens-100k_image_features_CLIPRN50.npy"),
        "video": np.load(DATA / "MicroLens-100k_video_features_VideoMAE.npy"),
    }
    if (DATA / "covers_siglip2.npy").exists():
        emb["cover_sl2"] = np.load(DATA / "covers_siglip2.npy").astype(np.float32)
    assert all(len(m) == len(df) for m in emb.values())
    return df, emb


def labels(df: pd.DataFrame) -> dict[str, np.ndarray]:
    """Two definitions of "trending". Likes are never a feature: they follow views, so they would leak the answer.

    raw          top 25% by views across all videos (the Passioné v1 rule)
    age_adjusted top 25% by views within each fifth of videos by age, so a video is only compared with videos
                 that had about as long to collect views
    """
    raw = (df["views"] >= df["views"].quantile(1 - TOP_SHARE)).astype(int).to_numpy()
    cohort = pd.qcut(df["age_days"], 5, labels=False)
    cut = df.groupby(cohort)["views"].transform(lambda v: v.quantile(1 - TOP_SHARE))
    adjusted = (df["views"] >= cut).astype(int).to_numpy()
    return {"raw": raw, "age_adjusted": adjusted}


def split(y: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """The same stratified 80/20 split for every model and feature set at a given seed, so comparisons are paired."""
    return train_test_split(np.arange(len(y)), test_size=TEST_SHARE, stratify=y, random_state=seed)


@dataclass
class Blocks:
    """Feature blocks for one split: train and test matrices per block, fit on train rows only."""

    train: dict[str, np.ndarray | csr_matrix]
    test: dict[str, np.ndarray | csr_matrix]


def sparse_blocks(names: list[str], df: pd.DataFrame, emb: dict, tr: np.ndarray, te: np.ndarray) -> Blocks:
    """Full-resolution blocks for the linear baseline: TF-IDF words plus standardised embeddings."""
    out_tr, out_te = {}, {}
    if "words" in names:
        tfidf = TfidfVectorizer(max_features=20000, ngram_range=(1, 2), min_df=2, sublinear_tf=True)
        length = df["title"].str.split().str.len().to_numpy(dtype=float)[:, None] / 20
        out_tr["words"] = hstack([tfidf.fit_transform(df["title"].iloc[tr]), csr_matrix(length[tr])]).tocsr()
        out_te["words"] = hstack([tfidf.transform(df["title"].iloc[te]), csr_matrix(length[te])]).tocsr()
    for name in EMBEDDINGS:
        if name in names:
            scaler = StandardScaler().fit(emb[name][tr])
            norm = np.sqrt(emb[name].shape[1])  # equal total weight per block, whatever its width
            out_tr[name] = scaler.transform(emb[name][tr]) / norm
            out_te[name] = scaler.transform(emb[name][te]) / norm
    return Blocks(out_tr, out_te)


def dense_blocks(names: list[str], df: pd.DataFrame, emb: dict, tr: np.ndarray, te: np.ndarray,
                 dims: int | None) -> Blocks:
    """Dense blocks for the non-linear models. With `dims`, each block is reduced to that many components (SVD for
    words, PCA for embeddings) so every modality has the same width; with None, embeddings keep their full width
    and words get a 256-component SVD."""
    out_tr, out_te = {}, {}
    if "words" in names:
        tfidf = TfidfVectorizer(max_features=20000, ngram_range=(1, 2), min_df=2, sublinear_tf=True)
        svd = TruncatedSVD(dims or 256, random_state=0)
        out_tr["words"] = svd.fit_transform(tfidf.fit_transform(df["title"].iloc[tr]))
        out_te["words"] = svd.transform(tfidf.transform(df["title"].iloc[te]))
        length = df["title"].str.split().str.len().to_numpy(dtype=float)[:, None]
        out_tr["words"] = np.hstack([out_tr["words"], length[tr]])
        out_te["words"] = np.hstack([out_te["words"], length[te]])
    for name in EMBEDDINGS:
        if name in names:
            scaler = StandardScaler().fit(emb[name][tr])
            x_tr, x_te = scaler.transform(emb[name][tr]), scaler.transform(emb[name][te])
            if dims:
                pca = PCA(dims, random_state=0).fit(x_tr)
                x_tr, x_te = pca.transform(x_tr), pca.transform(x_te)
            out_tr[name], out_te[name] = x_tr, x_te
    for blocks in (out_tr, out_te):  # put every dense block on the same scale
        for name, m in blocks.items():
            blocks[name] = m.astype(np.float32)
    mu = {n: out_tr[n].mean(0) for n in out_tr}
    sd = {n: out_tr[n].std(0) + 1e-6 for n in out_tr}
    return Blocks({n: (m - mu[n]) / sd[n] for n, m in out_tr.items()}, {n: (m - mu[n]) / sd[n] for n, m in out_te.items()})
