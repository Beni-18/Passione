# INTEGRATION.md — how the pieces plug together

Three people, three directories, two seams. **Neither seam is a Python import.**

```
frontend/  ──HTTP + JSON──▶  backend/  ──files on disk──▶  ml/
             API_CONTRACT.md              model bundle
   (UI)          (API)                    (training)
```

| Directory | Owner | Talks to the rest of the repo via |
|---|---|---|
| `frontend/` | UI owner | HTTP calls described in `docs/API_CONTRACT.md` |
| `backend/` | Backend owner | both seams |
| `ml/` | ML owner | two files written into `models/` — nothing else |

---

## Seam 1 — ML → backend

**For the ML owner. This section is the entire interface. If you satisfy it, your model works in the
service; nothing else about your code matters to the backend.**

You never import backend code and the backend never imports yours. The handoff is two files.

### File 1 — `models/model_v{N}.joblib`

One joblib bundle, three keys:

```python
import joblib

joblib.dump({
    "pipeline": fitted_sklearn_pipeline,   # .transform(pd.DataFrame) -> ndarray
    "model":    fitted_classifier,         # .predict_proba(X) -> [[p_not_trending, p_trending]]
    "meta": {
        "model_version":    "rf_v3",       # string, matches the file's v{N}
        "feature_names":    ["genre_Thriller", "upload_hour", "tag_count", ...],
        "known_categories": {              # used by the backend for grounding
            "genre":    ["Thriller", "Comedy", ...],
            "language": ["en", "hi", "ta", ...],
        },
        "encoder_version":  "enc_v1",
        "random_seed":      42,
        "trained_at":       "2026-08-06T18:55:00Z",   # ISO 8601, UTC
    },
}, "models/model_v3.joblib")
```

Column 1 of `predict_proba` output is the **trending** probability. Say so if your label encoding
differs — do not silently flip it.

### File 2 — `models/metrics_v{N}.json`

Written in the same run, same `N`:

```json
{
  "model_version": "rf_v3",
  "precision": 0.62,
  "recall": 0.48,
  "f1": 0.54,
  "roc_auc": 0.79,
  "accuracy": 0.91,
  "positive_rate": 0.07,
  "random_seed": 42,
  "split": { "train": 3500, "val": 750, "test": 750 },
  "trained_at": "2026-08-06T18:55:00Z"
}
```

All metrics are computed on the **held-out test split**, never on training data. `positive_rate` is
the share of trending rows in the training set — the backend surfaces it so nobody mistakes a 91%
accuracy on a 7% positive class for a good model.

### Five rules that make or break the handoff

1. **`pipeline.transform` receives a raw pandas DataFrame using the `/predict` field names:**
   `title, genre, duration_minutes, upload_time, language, tags` (tags is a list of strings).
   All feature engineering — upload-hour and day-of-week extraction, tag counting, one-hot or target
   encoding, any TF-IDF — happens **inside** the pipeline. The backend engineers nothing and will
   pass exactly those six fields. This is also a marked requirement: raw metadata may only reach the
   model through the versioned pipeline.

2. **Unseen categories must not raise.** A genre or language never seen in training will arrive.
   Configure encoders with `handle_unknown="infrequent_if_exist"` (or `"ignore"`), and list the real
   training categories in `meta.known_categories` so the backend can mark that prediction
   `grounded: false` instead of quietly scoring garbage.

3. **Fix the seed and record the split.** Two runs on the same CSV with the same seed must produce
   byte-identical metrics. This is scored with no partial credit. Seed every source of randomness:
   `train_test_split(random_state=seed)`, the classifier's `random_state`, any sampler or shuffle.

4. **Bump `N`. Never overwrite an existing artifact.** `model_v3.joblib` stays on disk when
   `model_v4.joblib` appears, so a bad retrain can be rolled back without retraining.

5. **Both files, or neither.** The backend treats a `.joblib` with no matching `metrics_v{N}.json` as
   an incomplete artifact and will refuse to serve it. Write metrics first, model second, if you want
   to be safe against a half-finished run being picked up.

### What the backend does with it

- Discovers `models/model_v*.joblib`, picks the highest version (or the one explicitly activated via
  `POST /models/activate`).
- Validates `meta`, then checks `roc_auc` against a configured `MIN_ROC_AUC` floor. **A model that
  finished `.fit()` but fails the floor is *trained*, not *ready*** — `/health` stays `degraded` and
  `/predict` keeps returning `grounded: false`.
- Keeps the previously loaded model live if a new artifact fails to load.
- Never fabricates a score. No model, unseen category, or confidence below the grounding threshold
  all produce `grounded: false` with a plain-language `reason`.

### Testing your artifact against the backend

```bash
python ml/src/train.py --csv data/train.csv --seed 42     # writes models/model_v1.joblib + metrics_v1.json
curl localhost:8000/health                                 # model_loaded should flip to true
curl localhost:8000/metrics                                # should echo your metrics_v1.json
curl -X POST localhost:8000/predict -H 'content-type: application/json' \
     -d @tests/fixtures/predict_ok.json                    # grounded: true
curl -X POST localhost:8000/predict -H 'content-type: application/json' \
     -d @tests/fixtures/predict_unseen.json                # grounded: false, with a reason
```

If the fourth call returns `grounded: false` when it shouldn't, the usual cause is
`meta.known_categories` missing or not matching the values your encoder actually learned.

---

## Seam 2 — backend → UI

**For the UI owner.** `docs/API_CONTRACT.md` is the source of truth for every shape. Rules:

- The UI holds no logic. It POSTs `/predict`, GETs `/status` and `/metrics`, and renders the JSON.
- `CORS_ORIGINS` is env-driven on the backend. Tell the backend owner your dev origin; don't expect
  a hardcoded one.
- **Additive changes only during the build window.** New optional response fields are safe; renaming
  or removing a field is not. Any unavoidable break gets announced explicitly.
- **Render the ungrounded case as prominently as the grounded one.** When `grounded` is false,
  `trending_probability` is `null` and `reason` explains why. A blank box where a score should be is
  a bug; "we can't confidently score this, and here's why" is the correct product behaviour and is
  directly worth marks.
- `/status` is a poll, not a stream. Poll it while a training job runs and show real
  `rows_processed` / `rows_failed` counts rather than a spinner.

---

## Escalation

If either seam turns out to be wrong — the bundle format can't carry something the model needs, or
the UI needs a shape the contract doesn't have — **raise it as a change, don't work around it.** A
private workaround on one side of a seam is how a working system becomes an unworkable one at 7pm.
