# Architecture

## Diagram

```
                 HTTP + JSON                    frozen Python import
                 (API_CONTRACT.md)               (mlcore.api)
  frontend/  ───────────────────▶  backend/  ───────────────────▶  ml/
    (UI)                             (API)                        (training)
                                        │
                                        ├── app/api/         routes, thin, validate → service → schema
                                        ├── app/schemas/      Pydantic v2 wire shapes
                                        ├── app/services/     business logic, incl. the grounding decision
                                        ├── app/ml_adapter/   the ONLY code that imports mlcore
                                        └── app/core/         config, errors, logging
```

## Why the pipeline is decoupled

Three people, three directories, two seams:

- `frontend/` never runs backend code — it only speaks HTTP against
  `docs/API_CONTRACT.md`. The UI can be replaced entirely without touching the API.
- `backend/` imports exactly six functions from one frozen module, `mlcore.api`
  (`docs/INTEGRATION.md` Seam 1), and only from one file: `app/ml_adapter/mlcore_client.py`.
  `mlcore`'s internals — algorithm, features, how a model gets fit and stored — are free to change
  as long as those six signatures and shapes hold. This is a narrower seam than "no Python import
  at all," but it's still exactly one file wide: nothing else in `backend/` knows `mlcore` exists.

This means the ML model and the real UI can land "suddenly and late" (CLAUDE.md section 1)
without anyone rewriting `backend/`. Until real training lands, the service still boots and
answers honestly: `mlcore`'s dummy implementation keeps `/health` at `"degraded"` and `/predict`
at `grounded: false` rather than fabricating a score, and `mlcore_client.py` never trusts that
`mlcore` "never raises" — every one of the six calls is wrapped in try/except and degrades to the
same ungrounded shape on an unexpected exception.

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
