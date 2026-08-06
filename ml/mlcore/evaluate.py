"""All evaluation metrics (plan §10). Returns a plain dict; decides nothing.

Deliberately includes the majority-baseline accuracy and positive rate
alongside every other number — the handout calls out "95% accuracy by always
predicting not-trending" as the trap this exists to make impossible to hide.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def evaluate(y_test, proba: np.ndarray, threshold: float = 0.5) -> dict:
    y_test = np.asarray(y_test)
    pred = (proba >= threshold).astype(int)

    positive_rate = float(y_test.mean())
    majority_baseline_accuracy = float(max(positive_rate, 1 - positive_rate))

    tn, fp, fn, tp = confusion_matrix(y_test, pred, labels=[0, 1]).ravel()

    return {
        "roc_auc": float(roc_auc_score(y_test, proba)),
        "pr_auc": float(average_precision_score(y_test, proba)),
        "precision": float(precision_score(y_test, pred, zero_division=0)),
        "recall": float(recall_score(y_test, pred, zero_division=0)),
        "f1": float(f1_score(y_test, pred, zero_division=0)),
        "accuracy": float(accuracy_score(y_test, pred)),
        "majority_baseline_accuracy": majority_baseline_accuracy,
        "positive_rate": positive_rate,
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "n_test": int(len(y_test)),
        "n_positive_test": int(y_test.sum()),
    }
