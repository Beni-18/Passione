#!/usr/bin/env python3
"""Minimum EDA (plan §8). ~10 minutes of work, run once. Catches data bugs
and feeds REPORT.md §9.2 — not exploratory. Prints to console and writes
artifacts/eda_summary.json.

Usage: python3 ml/scripts/eda.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from mlcore import config  # noqa: E402
from mlcore.adapters import load_training_frame  # noqa: E402
from mlcore.features import build_features  # noqa: E402


def main() -> int:
    print(f"Loading {config.DEFAULT_TRAIN_CSV} ...")
    res = load_training_frame(config.DEFAULT_TRAIN_CSV)
    canonical_df, y, threshold = res["canonical_df"], res["y"], res["threshold"]
    X, _ = build_features(canonical_df)

    summary = {}

    # 1. shape + duplicate-id check
    summary["rows_received"] = res["rows_received"]
    summary["rows_processed"] = res["rows_processed"]
    summary["rows_failed"] = res["rows_failed"]
    dup_ids = int(canonical_df["id"].duplicated().sum())
    summary["duplicate_ids"] = dup_ids
    print(f"\n1. Rows: received={res['rows_received']} processed={res['rows_processed']} "
          f"failed={res['rows_failed']} | duplicate ids={dup_ids} (expect 0)")

    # 2. null counts
    null_counts = canonical_df[["title", "genre", "duration_minutes", "upload_time", "language"]].isna().sum()
    summary["null_counts"] = {k: int(v) for k, v in null_counts.items()}
    print(f"\n2. Null counts:\n{null_counts}")

    # 3. class balance
    positive_rate = float(y.mean())
    summary["positive_rate"] = positive_rate
    summary["popularity_threshold"] = threshold
    print(f"\n3. Positive rate: {positive_rate:.4f} (threshold at {config.POPULARITY_PERCENTILE:.0%} "
          f"percentile = {threshold:.4f})")

    # 4. popularity distribution
    pop_describe = canonical_df["popularity"].describe()
    summary["popularity_describe"] = {k: float(v) for k, v in pop_describe.items()}
    print(f"\n4. popularity describe():\n{pop_describe}")

    # 5. genre frequency + positive rate per genre
    genre_stats = X.assign(y=y.values).groupby("primary_genre")["y"].agg(["count", "mean"]) \
        .sort_values("count", ascending=False).head(10)
    summary["top_genres"] = {
        g: {"count": int(row["count"]), "positive_rate": float(row["mean"])}
        for g, row in genre_stats.iterrows()
    }
    print(f"\n5. Top 10 genres (count, positive_rate):\n{genre_stats}")

    # 6. positive rate by release_month / is_friday_release
    month_stats = X.assign(y=y.values).groupby("release_month")["y"].mean().sort_index()
    friday_stats = X.assign(y=y.values).groupby("is_friday_release")["y"].mean()
    summary["positive_rate_by_month"] = {k: float(v) for k, v in month_stats.items()}
    summary["positive_rate_by_friday_release"] = {str(k): float(v) for k, v in friday_stats.items()}
    print(f"\n6. Positive rate by release_month:\n{month_stats}")
    print(f"\n   Positive rate by is_friday_release:\n{friday_stats}")

    # 7. tag_count / duration_minutes describe
    tag_desc = X["tag_count"].describe()
    dur_desc = X["duration_minutes"].describe()
    dur_null_rate = float(canonical_df["duration_minutes"].isna().mean())
    summary["tag_count_describe"] = {k: float(v) for k, v in tag_desc.items()}
    summary["duration_minutes_describe"] = {k: float(v) for k, v in dur_desc.items()}
    summary["duration_minutes_null_rate"] = dur_null_rate
    print(f"\n7. tag_count describe():\n{tag_desc}")
    print(f"\n   duration_minutes describe() (null rate={dur_null_rate:.4f}):\n{dur_desc}")

    # Tier-2 correlation check (plan §5's report finding) — one check each, not exploration.
    raw = pd.read_csv(config.DEFAULT_TRAIN_CSV)
    tier2_corr = {}
    for col in ["budget", "vote_count", "revenue", "vote_average"]:
        if col in raw.columns:
            tier2_corr[col] = float(pd.to_numeric(raw[col], errors="coerce").corr(raw["popularity"]))
    summary["tier2_leakage_correlations"] = tier2_corr
    print(f"\nTier-2 / leakage correlations with popularity (report §5, §9.2):\n{json.dumps(tier2_corr, indent=2)}")

    config.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    config.EDA_SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True, default=str))
    print(f"\nWrote {config.EDA_SUMMARY_PATH}")

    if not (0.20 <= positive_rate <= 0.60):
        print(f"\nWARNING: positive rate {positive_rate:.4f} is outside the healthy 20-60% band.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
