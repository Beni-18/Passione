# Architecture

## Diagram

```
                 HTTP + JSON                    files on disk
                 (API_CONTRACT.md)               (model bundle)
  frontend/  ───────────────────▶  backend/  ───────────────────▶  ml/
    (UI)                             (API)                        (training)
                                        │
                                        ├── app/api/         routes, thin, validate → service → schema
                                        ├── app/schemas/      Pydantic v2 wire shapes
                                        ├── app/services/     business logic, incl. the grounding decision
                                        ├── app/ml_adapter/   the ONLY code that knows a model exists
                                        └── app/core/         config, errors, logging
```

## Why the pipeline is decoupled

Three people, three directories, two seams, **neither seam a Python import**:

- `frontend/` never runs backend code — it only speaks HTTP against
  `docs/API_CONTRACT.md`. The UI can be replaced entirely without touching the API.
- `backend/` never imports `ml/` — it reads two files
  (`models/model_v{N}.joblib`, `models/metrics_v{N}.json`) through
  `app/ml_adapter/`, per `docs/INTEGRATION.md`. Swapping in a real model changes exactly one file:
  `joblib_loader.py`.

This means the ML model and the real UI can land "suddenly and late" (CLAUDE.md section 1)
without anyone rewriting `backend/`. Until they land, the service still boots and answers
honestly: `ml_adapter/stub.py` keeps `/health` at `"degraded"` and `/predict` at
`grounded: false` rather than fabricating a score.

## Why routes are thin

Every route validates a request, calls exactly one service function, and returns a schema. The
grounding decision — whether a prediction is confident enough to serve — lives in
`prediction_service.py`, not in `routes/predict.py`, so it can be unit-tested without spinning up
HTTP and so the route body never grows past the point where its logic is obvious at a glance.

## Why `/train` is async

Training a model on thousands of rows cannot happen inside a single HTTP request without either
blocking the event loop or requiring a client to hold a connection open for the run's duration.
`/train` returns `202` immediately with a `job_id`; `/status` is a poll, not a stream, and reports
real row counts (`rows_processed`, `rows_failed`) rather than a spinner.

## Why evaluation is honest by construction

`/health` is not `"ok"` until a model is both loaded *and* clears `MIN_ROC_AUC` — a model that
finished `.fit()` but underperforms is "trained", not "ready". `/predict` marks a prediction
`grounded: false` with a plain-language `reason` whenever the category is unseen or confidence is
below `GROUNDING_MIN_CONFIDENCE`, rather than returning a number that looks the same whether or
not the model actually knows anything about the input.
