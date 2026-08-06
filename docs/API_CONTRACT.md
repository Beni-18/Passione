# API Contract — Passioné

Source of truth shared with the UI owner. Mirrors CLAUDE.md section 5 and the actual routes under
`backend/app/api/routes/`. Base URL: `http://localhost:8000`.

## Error envelope

Every non-2xx response uses this shape:

```json
{ "error": { "code": "MODEL_NOT_READY", "message": "No trained model is loaded.", "detail": null } }
```

| Code | HTTP status | Raised by |
|---|---|---|
| `VALIDATION_ERROR` | 422 | Any request that fails Pydantic validation |
| `MODEL_NOT_READY` | 409 | `GET /metrics`, `POST /models/activate` when no model is loaded |
| `JOB_NOT_FOUND` | 404 | `GET /status` with an unknown `job_id` |
| `EMPTY_DATASET` | 400 | `POST /train` with zero data rows (empty or header-only CSV) |
| `BAD_CSV` | 400 | `POST /train` with an unparseable file or missing `file`/`csv_path` |

## GET /health

```json
{ "status": "ok", "model_loaded": true, "model_version": "rf_v3", "enrichment_api_connected": true }
```

`status` is `"ok"` only when a trained model is loaded *and* its metrics cleared `MIN_ROC_AUC`,
otherwise `"degraded"`. **Current build state: no model exists yet, so this always returns
`"degraded"` / `model_loaded: false` / `model_version: null`.**

## POST /train

Accepts either a JSON body or a multipart file upload.

- JSON: `{"csv_path": "...", "random_seed": 42}`
- Multipart: `file=<csv>` (optional `random_seed` form field, default `42`)

```json
{ "job_id": "t3f1a2c9", "rows_received": 5000, "status": "queued" }
```
`202 Accepted`. Raises `EMPTY_DATASET` (400) if the CSV has zero data rows, `BAD_CSV` (400) if
neither `file` nor `csv_path` is provided or the file can't be parsed.

**Current build state: the job and row count are real (backend-counted before mlcore is ever
called); the fit itself is mlcore's dummy `train_model()` (docs/INTEGRATION.md Seam 1), which
reports `rows_processed: 0` and no metrics regardless of input.**

## GET /status?job_id=...

```json
{ "job_id": "t3f1a2c9", "status": "training", "rows_total": 5000, "rows_processed": 3200,
  "rows_failed": 4, "message": null, "metrics": null, "model_version": null }
```
`status` is one of `queued | training | complete | failed`. Raises `JOB_NOT_FOUND` (404) for an
unknown `job_id`.

## POST /predict

```json
{ "title": "Midnight Run", "genre": "Thriller", "duration_minutes": 24,
  "upload_time": "2026-08-06T18:30:00Z", "language": "en",
  "tags": ["suspense", "indie", "short-film"] }
```

Grounded response:
```json
{ "trending_probability": 0.71, "predicted_label": "trending", "model_version": "rf_v3",
  "top_features": ["genre=Thriller", "upload_hour=18", "tag_count=3"],
  "grounded": true, "reason": null }
```

Ungrounded response (no model, unseen category, or confidence under `GROUNDING_MIN_CONFIDENCE`):
```json
{ "trending_probability": null, "predicted_label": "unknown", "model_version": "dummy_v0",
  "top_features": [], "grounded": false,
  "reason": "No trained model loaded yet (dummy pipeline stage)." }
```
Note `model_version` may be non-null even when ungrounded — it identifies whatever mlcore build is
running, not whether that build's model is ready to score anything.

Missing a required field returns `VALIDATION_ERROR` (422), not a 200 with a null score.

**Current build state: always returns the ungrounded shape above — mlcore's `predict()` is still
the dummy implementation (docs/INTEGRATION.md Seam 1).**

## GET /metrics

Last run's held-out evaluation, sourced from `mlcore.get_model_metadata()` via
`backend/app/ml_adapter/mlcore_client.py` (docs/INTEGRATION.md Seam 1):

```json
{ "model_version": "rf_v3", "precision": 0.62, "recall": 0.48, "f1": 0.54, "roc_auc": 0.79,
  "accuracy": 0.91, "positive_rate": 0.07, "random_seed": 42,
  "split": { "train": 3500, "val": 750, "test": 750 }, "trained_at": "2026-08-06T18:55:00Z" }
```
`split.val` has no source in mlcore's current metadata shape (it reports `n_train`/`n_test` but no
validation count) — it's hardcoded to `0` until that's resolved with the ML owner.

**Current build state: raises `MODEL_NOT_READY` (409) — mlcore's `get_model_metadata()` always
reports `passed_gate: false` at this stage, so there is nothing to report.**

## GET /models

```json
{ "active": "rf_v3", "available": ["rf_v3", "rf_v2", "logreg_v1"] }
```
Note: mlcore's frozen interface has no "list all versions" call — `available` can only ever
contain the single currently-loaded version (or be empty), never real version history. See
docs/INTEGRATION.md Seam 1.

**Current build state: `{"active": null, "available": []}` — mlcore reports no model loaded yet.**

## POST /models/activate

```json
{ "model_version": "rf_v2" }
```
→
```json
{ "active": "rf_v2" }
```
Raises `MODEL_NOT_READY` (409) if `mlcore.load_model()` reports `loaded: false`.
**Current build state: always raises `MODEL_NOT_READY` — mlcore's `load_model()` is still a no-op.**

## GET /

Service banner, not part of the versioned contract:
```json
{ "service": "Passioné", "status": "running" }
```

---

## Change log

| Date | Change |
|---|---|
| 2026-08-06 | Initial contract, mirrors CLAUDE.md section 5. Phase 1 skeleton: all endpoints live, `/predict` always ungrounded, `/metrics` and `/models/activate` always 409, `/health` always degraded. |
| 2026-08-06 | ML integration seam changed from a `models/*.joblib` file handoff to a frozen `mlcore.api` import (docs/INTEGRATION.md Seam 1). No response field names or shapes changed — only the internal source of the (still-dummy) values, and the fact that `model_version` can now be non-null even in an ungrounded response. |
