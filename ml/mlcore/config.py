"""All tunable constants live here, and only here. No logic in this file.

Every value below is env-overridable so the backend/deploy layer can point at a
different artifacts directory or data file without touching code.
"""
from __future__ import annotations

import os
from pathlib import Path

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
ML_ROOT = Path(__file__).resolve().parents[1]          # .../ml (mlcore/config.py -> mlcore -> ml)
RAW_DATA_DIR = Path(os.environ.get("ML_RAW_DATA_DIR", ML_ROOT / "data" / "raw"))
PROCESSED_DATA_DIR = Path(os.environ.get("ML_PROCESSED_DATA_DIR", ML_ROOT / "data" / "processed"))
SAMPLES_DIR = Path(os.environ.get("ML_SAMPLES_DIR", ML_ROOT / "data" / "samples"))
ARTIFACTS_DIR = Path(os.environ.get("ML_ARTIFACTS_DIR", ML_ROOT / "artifacts"))
DEFAULT_TRAIN_CSV = RAW_DATA_DIR / "movies_train.csv"
LATEST_POINTER_PATH = ARTIFACTS_DIR / "latest.json"
EDA_SUMMARY_PATH = ARTIFACTS_DIR / "eda_summary.json"

# --------------------------------------------------------------------------
# Reproducibility (handout Part 5 — no partial credit)
# --------------------------------------------------------------------------
SEED = 42
TEST_SIZE = 0.2

# --------------------------------------------------------------------------
# Target definition (plan §4) — computed ONCE on the full training file and
# frozen into metrics.json. Never recompute per fold or per rerun.
# --------------------------------------------------------------------------
POPULARITY_PERCENTILE = 0.75

# --------------------------------------------------------------------------
# Honesty gate (plan §10 / §12)
# --------------------------------------------------------------------------
MIN_ROC_AUC = 0.60
UNCERTAIN_BAND = (0.45, 0.55)

# Promotion rule (plan §9): a new model version only overwrites `latest.json`
# if it beats the incumbent's test ROC-AUC by at least this much.
PROMOTION_MARGIN = 0.01

# --------------------------------------------------------------------------
# Model hyperparameters
# --------------------------------------------------------------------------
LOGREG_PARAMS = dict(class_weight="balanced", max_iter=1000, random_state=SEED)
RF_PARAMS = dict(
    n_estimators=300,
    min_samples_leaf=5,
    class_weight="balanced_subsample",
    random_state=SEED,
    n_jobs=-1,
)

# --------------------------------------------------------------------------
# Preprocessing
# --------------------------------------------------------------------------
ONEHOT_MIN_FREQUENCY = 10

CATEGORICAL_FEATURES = ["primary_genre", "language", "release_month", "release_dayofweek"]
NUMERIC_FEATURES = ["duration_minutes", "release_year", "tag_count", "title_length", "title_word_count",
                     "title_caps_ratio"]
BOOL_FEATURES = ["duration_missing", "is_holiday_season", "is_friday_release", "has_tags",
                  "title_has_punctuation_hook", "title_has_number"]
ALL_FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES + BOOL_FEATURES

# Display-name map for human-readable top_features strings, e.g. "genre=Thriller".
DISPLAY_NAMES = {
    "primary_genre": "genre",
    "language": "language",
    "release_month": "release_month",
    "release_dayofweek": "release_dayofweek",
    "duration_minutes": "duration_minutes",
    "release_year": "release_year",
    "tag_count": "tag_count",
    "title_length": "title_length",
    "title_word_count": "title_word_count",
    "title_caps_ratio": "title_caps_ratio",
    "duration_missing": "duration_missing",
    "is_holiday_season": "is_holiday_season",
    "is_friday_release": "is_friday_release",
    "has_tags": "has_tags",
    "title_has_punctuation_hook": "title_has_punctuation_hook",
    "title_has_number": "title_has_number",
}
