"""The single shared feature code path (plan §1, §6). Runs identically at
train time (on the full canonical_df from adapters.py) and at serve time (on
a 1-row canonical_df built from schema.validate_metadata()).

PURE, deterministic, no fitting, no I/O, no fallback to any column that isn't
in the /predict contract (see plan §5's Tier-1/Tier-2 split — only Tier-1
columns are used here).
"""
from __future__ import annotations

import pandas as pd

from mlcore import config

_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _title_caps_ratio(title: str) -> float:
    letters = [c for c in title if c.isalpha()]
    if not letters:
        return 0.0
    caps = sum(1 for c in letters if c.isupper())
    return caps / len(letters)


def build_features(canonical_df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """canonical_df has the contract-shaped columns produced by adapters.py /
    schema.validate_metadata(): title, genre, duration_minutes, upload_time,
    language, tags. Returns (X_df, feature_names) where X_df has exactly
    config.ALL_FEATURES as columns, in that explicit, deterministic order.
    """
    df = canonical_df.copy()

    title = df["title"].fillna("").astype(str)
    tags = df["tags"].apply(lambda t: t if isinstance(t, list) else [])
    upload_time = pd.to_datetime(df["upload_time"], errors="coerce")

    out = pd.DataFrame(index=df.index)

    # --- categorical -------------------------------------------------------
    out["primary_genre"] = df["genre"].apply(lambda g: str(g).strip() if pd.notna(g) and str(g).strip() else "unknown")
    out["language"] = df["language"].apply(lambda l: str(l).strip() if pd.notna(l) and str(l).strip() else "unknown")
    out["release_month"] = upload_time.dt.month.apply(lambda m: f"{int(m):02d}" if pd.notna(m) else "unknown")
    out["release_dayofweek"] = upload_time.dt.dayofweek.apply(
        lambda d: _DAY_NAMES[int(d)] if pd.notna(d) else "unknown"
    )

    # --- numeric -------------------------------------------------------------
    out["duration_minutes"] = pd.to_numeric(df["duration_minutes"], errors="coerce")
    out["release_year"] = upload_time.dt.year.astype("float")
    out["tag_count"] = tags.apply(len).astype(float)
    out["title_length"] = title.apply(len).astype(float)
    out["title_word_count"] = title.apply(lambda t: len(t.split())).astype(float)
    out["title_caps_ratio"] = title.apply(_title_caps_ratio)

    # --- bool ----------------------------------------------------------------
    out["duration_missing"] = df["duration_minutes"].isna()
    month_num = upload_time.dt.month
    dow_num = upload_time.dt.dayofweek
    out["is_holiday_season"] = month_num.isin([11, 12]).fillna(False)
    out["is_friday_release"] = (dow_num == 4).fillna(False)
    out["has_tags"] = out["tag_count"] > 0
    out["title_has_punctuation_hook"] = title.apply(lambda t: any(ch in "!?" for ch in t))
    out["title_has_number"] = title.apply(lambda t: any(ch.isdigit() for ch in t))

    out = out[config.ALL_FEATURES]
    return out, list(config.ALL_FEATURES)
