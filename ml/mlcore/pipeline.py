"""sklearn Pipeline construction (plan §7). Loads no data; purely structural.

Everything — encoder + estimator — lives in ONE Pipeline, fit once, serialized
as one artifact. This makes train/serve skew structurally impossible: the
exact fitted encoder that produced training features is the same object
scoring a live /predict row.
"""
from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from mlcore import config


def make_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(
                    handle_unknown="infrequent_if_exist",
                    min_frequency=config.ONEHOT_MIN_FREQUENCY,
                    sparse_output=False,
                ),
                config.CATEGORICAL_FEATURES,
            ),
            (
                "num",
                Pipeline([
                    ("impute", SimpleImputer(strategy="median", add_indicator=True)),
                    ("scale", StandardScaler()),
                ]),
                config.NUMERIC_FEATURES,
            ),
            ("bool", "passthrough", config.BOOL_FEATURES),
        ],
        remainder="drop",  # deliberate: an unexpected column must never reach the model
    )


def make_pipeline(algo: str = "logreg") -> Pipeline:
    """algo in {'dummy', 'logreg', 'random_forest'}."""
    preprocessor = make_preprocessor()
    if algo == "dummy":
        estimator = DummyClassifier(strategy="prior", random_state=config.SEED)
    elif algo == "logreg":
        estimator = LogisticRegression(**config.LOGREG_PARAMS)
    elif algo == "random_forest":
        estimator = RandomForestClassifier(**config.RF_PARAMS)
    else:
        raise ValueError(f"Unknown algo: {algo!r}")
    return Pipeline([("preprocess", preprocessor), ("model", estimator)])
