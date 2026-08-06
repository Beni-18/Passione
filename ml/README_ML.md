# ML Pipeline — Status and Integration Notes

`mlcore` is done and trained. This documents current state, not a wiring tutorial — the backend
side (`backend/app/ml_adapter/mlcore_client.py`) is already built against the six frozen functions
per `docs/INTEGRATION.md` Seam 1, and needs no changes for this to work.

## How it's installed

```bash
pip install -r ml/requirements.txt && pip install --no-deps -e ml   # matches .github/workflows/ci.yml
```

`ml/mlcore/` is the real implementation now (was a dummy `grounded: false` stub through M0–M2 of
the build). Package layout and `ml/pyproject.toml` are unchanged — nothing outside `ml/` needed to
move or change for this swap.

## Current model status

- **Active (`latest.json`):** `rf_v1` (Random Forest) — test ROC-AUC **0.858**.
- **Also trained, not active:** `lr_v1` (Logistic Regression) — test ROC-AUC 0.848. `rf_v1` was
  promoted manually; it beat `lr_v1` by only +0.0097, under the codebase's own 0.01 auto-promotion
  margin, so this was a deliberate override, not an automated decision. See `REPORT.md` for the
  reasoning.
- Both clear the backend's `MIN_ROC_AUC = 0.65` readiness gate (`backend/app/core/config.py`)
  comfortably — `/health` reports `"ok"` once a model is loaded.
- Trained on `movies_train.csv` (Kaggle *Movie Popularity Prediction*), label = top-25th-percentile
  popularity, positive rate 25.0%, seed 42, deterministic split (see `ml/artifacts/rf_v1/split.json`).

## Sample `/predict` response (real, from the active model)

```json
{
  "trending_probability": 0.3891,
  "predicted_label": "not_trending",
  "predicted_label_display": "Not Trending",
  "confidence": 0.6109,
  "confidence_band": "medium",
  "model_version": "rf_v1",
  "top_features": ["tag_count=3.0", "duration_minutes=24.0", "release_year=2026.0"],
  "grounded": true,
  "reason": null,
  "errors": [],
  "unknown_fields": []
}
```

`predicted_label` is lowercase (`trending` / `not_trending` / `uncertain`); the backend's own
`_LABEL_MAP` in `mlcore_client.py` maps `"uncertain"` to its schema's `"unknown"`, which is expected
and by design (see `docs/INTEGRATION.md`'s field-mapping note — mlcore's extra fields, including
`predicted_label_display`, are intentionally not forwarded past the adapter).

**`grounded: false` is a normal, expected state** — surfaced whenever the model can't confidently
score a request (unseen genre/language, missing fields, or a probability in the 0.45–0.55 uncertain
band). The backend already renders this correctly per `docs/INTEGRATION.md` Seam 1: `grounded`,
`predicted_label`, and `reason` pass through from mlcore unmodified, no backend recomputation.

## /predict field mapping (context — never needs touching on the backend side)

| Contract field you send | What it trains on |
|---|---|
| `genre` | primary (first-listed) genre — real, not a proxy |
| `duration_minutes` | movie runtime — real, modeled |
| `upload_time` | movie release date (reframed — see `REPORT.md` §9.2) |
| `language` | original language — real, not a proxy |
| `tags` | movie keywords |
| `title` | title-shape features (length, word count, punctuation, etc.) |

## Known integration risks — raised per docs/INTEGRATION.md Seam 1 rule 3 ("raise it, don't work around it")

**1. Dependency version mismatch (`ml/requirements.txt` vs `backend/requirements.txt`) — tested, mixed result.**
`ml/requirements.txt` pins `scikit-learn==1.8.0`, `pandas==2.3.3`, `joblib==1.5.3` — the exact
versions `ml/artifacts/{lr_v1,rf_v1}/model.joblib` were actually fit and pickled with.
`backend/requirements.txt` pins the older `scikit-learn==1.6.0`, `pandas==2.2.3`, `joblib==1.4.2`.

Tested directly (isolated venv, backend's exact older pins, loading each `model.joblib` and calling
`predict_proba`):
- **`rf_v1` (the currently active model) loads and predicts correctly** under the older pins —
  only `InconsistentVersionWarning`s, no functional failure.
- **`lr_v1` crashes** under the older pins: `AttributeError: 'LogisticRegression' object has no
  attribute 'multi_class'`. A real, sklearn-internal breaking change between 1.6.0 and 1.8.0, not a
  bug in this code.

**Practically low-risk today, but fragile:** the documented CI/Docker install order is
`backend/requirements.txt` *then* `ml/requirements.txt` — pip resolves sequentially, so the second
install upgrades scikit-learn/pandas/joblib to the 1.8.0/2.3.3/1.5.3 pins for the actual running
environment (verified: a fresh venv installed in that exact order ends up on 1.8.0, and both
`ml/scripts/smoke_test.py` and `check_reproducibility.py` pass under it). So today, with `rf_v1`
active, this isn't broken. It becomes broken silently if: (a) the install order ever changes, (b)
`lr_v1` is ever activated via `POST /models/activate` under an environment that kept the older
pins, or (c) `backend/requirements.txt` gets installed *after* `ml/requirements.txt` in some future
CI/Docker change. `backend/requirements.txt`'s own pins are also currently misleading — they're
never actually what's running, since `ml/requirements.txt` silently overrides them on install.
Recommend the two files agree on one explicit set of versions rather than relying on install-order
to paper over the difference.

**2. `tests/test_reproducibility.py` calls `mlcore.api.train_model()` directly against
`data/samples/clean_50.csv`**, which is shaped as `title,genre,duration_minutes,upload_time,
language,tags,views` — the six `/predict` contract fields plus a `views` column. `mlcore`'s
`movie_to_canonical()` adapter (`ml/mlcore/adapters.py`) expects the raw Kaggle schema instead
(`id, title, genres, runtime, release_date, original_language, keywords, popularity`) — this is
the format the actual training dataset (`ml/data/raw/movies_train.csv`) comes in, and what all the
feature engineering and leakage analysis in `REPORT.md` was built against. These two schemas do
not match, and this was never exercised against real code before this merge — the dummy-stage
`train_model()` ignored its input entirely, so the mismatch was invisible until now. **This needs a
team decision, not a unilateral fix**, since it touches both sides:
  - Option A: point `tests/test_reproducibility.py` at `ml/data/samples/sample_small.csv` (real
    Kaggle-schema fixture, already committed) instead of `data/samples/clean_50.csv`.
  - Option B: `movie_to_canonical()` gains a second, contract-schema-shaped adapter path — real
    scope, would need its own label definition (percentile of `views`?) and leakage review, not a
    quick fix.
  - Option C: `clean_50.csv` gets regenerated in the raw Kaggle schema.

## Verification

```bash
python3 ml/scripts/smoke_test.py            # 40 hostile-input + end-to-end assertions (mlcore-internal)
python3 ml/scripts/check_reproducibility.py  # the 10-mark, no-partial-credit gate (mlcore-internal)
python3 ml/scripts/eda.py                    # regenerates artifacts/eda_summary.json
python -m pytest tests -v                    # the team's shared suite (from repo root) — see risk #2 above
```
