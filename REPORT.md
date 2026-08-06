# Passioné — Report

Graded write-up. Filled in at the end of the build, not during scaffolding — sections below are
stubs marking what must be filled and by when, so nothing is forgotten at freeze time.

## 1. Problem and label definition

**Decision (2026-08-06):** `trending = True` for the top 20% of rows by `views` within the
training dataset. Chosen over an absolute view-count threshold because it's dataset-agnostic and
gives a known, stable positive rate (~20%) regardless of how large or popular the training set is
— an absolute cutoff would swing the positive rate unpredictably between datasets. Chosen over a
10% threshold to keep enough positive examples for a small dataset to learn from, and over an
engagement-rate label because the sample data only reliably carries `views`.

_TODO once ml/ lands: confirm the ML owner implemented the label this way, and report the actual
resulting positive rate alongside the target 20%._

## 2. Data

_TODO: dataset source, size, class balance before and after any handling strategy._

## 3. Methods

**Imbalance strategy (decided 2026-08-06):** `class_weight="balanced"` on the classifier. Chosen
over SMOTE/undersampling because it's a single sklearn argument, requires no second seed to pin
for reproducibility, and doesn't fabricate or discard rows — important given
`tests/test_reproducibility.py` asserts byte-identical metrics across two runs on the same seed.

**Readiness/grounding thresholds (decided 2026-08-06):**
- `MIN_ROC_AUC = 0.65` — gates `GET /health` readiness (`backend/app/core/config.py`).
- `GROUNDING_MIN_CONFIDENCE = 0.60` — gates `grounded: false` in `POST /predict`.
Both are the config module's defaults already; chosen as a modest-but-real bar rather than a
lenient one, so a passing `/health` actually means something.

**Enrichment (decided 2026-08-06):** metadata-only for the build window — `ENRICHMENT_ENABLED`
defaults to `false`. TMDB's live client (`enrichment.py`) exists and fails open, but is not
switched on until the core pipe-then-model build order (CLAUDE.md section 8) is working, per the
project's own guidance to "enrich only after everything above works."

_TODO: feature set, model type(s) tried, and the reasoning behind the model choice — this is
graded on whether we *chose* rather than *defaulted*._

| Model | Precision | Recall | F1 | ROC-AUC | Accuracy |
|---|---|---|---|---|---|
| _TODO_ | | | | | |

## 4. Serving and evaluation honesty

_TODO: describe the grounding mechanism (unseen-category and low-confidence handling), and how
`/health` and `/metrics` avoid presenting an unqualified score._

## 5. Reproducibility

_TODO: evidence that two training runs on the same seed produce identical metrics
(`tests/test_reproducibility.py`)._

## 6. Limitations

_TODO: known weaknesses — dataset size, label proxy quality, features not yet used, anything the
grading rubric should be told about rather than discovered._

## 7. What we'd do next

_TODO._
