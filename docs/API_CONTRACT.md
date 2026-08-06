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

**Current build state: phase 1 skeleton. The job is real (row count, job_id) but the "training"
behind it is a dummy background task — it writes canned metrics rather than fitting a model.**

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
{ "trending_probability": null, "predicted_label": "unknown", "model_version": null,
  "top_features": [], "grounded": false,
  "reason": "No trained model is loaded yet." }
```

Missing a required field returns `VALIDATION_ERROR` (422), not a 200 with a null score.

**Current build state: always returns the ungrounded shape above — no model is loaded yet.**

## GET /metrics

Last run's held-out evaluation, read straight from `metrics_v{N}.json`:

```json
{ "model_version": "rf_v3", "precision": 0.62, "recall": 0.48, "f1": 0.54, "roc_auc": 0.79,
  "accuracy": 0.91, "positive_rate": 0.07, "random_seed": 42,
  "split": { "train": 3500, "val": 750, "test": 750 }, "trained_at": "2026-08-06T18:55:00Z" }
```

**Current build state: raises `MODEL_NOT_READY` (409) — no model is loaded yet, so there is
nothing to report.**

## GET /models

```json
{ "active": "rf_v3", "available": ["rf_v3", "rf_v2", "logreg_v1"] }
```
**Current build state: `{"active": null, "available": []}` — no artifacts on disk yet.**

## POST /models/activate

```json
{ "model_version": "rf_v2" }
```
→
```json
{ "active": "rf_v2" }
```
Raises `MODEL_NOT_READY` (409) if `model_version` doesn't correspond to a discovered artifact.
**Current build state: always raises `MODEL_NOT_READY` — no artifacts exist to activate.**

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
