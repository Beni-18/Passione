# CLAUDE.md — Passioné (backend)

Standing instructions for Claude Code in this repository. Read this file in full before writing any
code. Binding for every session, not just the first one.

Two companion docs, both of which you must read before touching the API surface or the model loader:
- `docs/API_CONTRACT.md` — request/response shapes, shared with the UI owner.
- `docs/INTEGRATION.md` — the model-artifact handoff format, owned jointly with the ML owner.

---

## 1. What we are building

**Passioné** — a service that takes the metadata of a newly uploaded movie or short film (genre,
duration, upload time, language, tags) and returns a trending-likelihood score, with honest
evaluation metrics behind it.

> **Naming rule:** the product is called **Passioné** everywhere a human can see it — the UI, the
> page title, the README heading, the API's `app_name`. Do not put any event, college, or
> competition name into the site, the UI copy, or user-facing strings.

Three people work on this repo:

| Area | Owner | Directory |
|---|---|---|
| **Backend (FastAPI)** | **Me — the person you are talking to** | `backend/` |
| ML model + training | Teammate A | `ml/` |
| UI | Teammate B | `frontend/` |

We coordinate through GitHub. The ML model and the real UI will land **suddenly and late**. The
entire structure below exists so that when they land, nothing in `backend/` has to be rewritten.

### What "done" means

A model in a notebook is not the deliverable. The deliverable is: someone submits metadata for
content we have never seen, and gets a scored, versioned, honestly-qualified answer back, from a
service they started with one command, with nobody from our team present.

Two classic failures to avoid:
- A model with no serving layer — training happened, getting a prediction out is now someone's problem.
- A model with no honest evaluation — a confident score whether or not the pattern is real. Worse
  than useless, because people spend promotion budget on it.

---

## 2. NON-NEGOTIABLE: the API surface report

**At the end of EVERY execution in which you touched anything under `backend/`, print an API surface
report.** No exceptions — not for refactors, not for one-line fixes, not when you are in a hurry.
It goes at the very end of your message, after your summary of the work.

```
=== API SURFACE REPORT ===
Changed this run:
  [ADDED]    POST /models/activate  -> backend/app/api/routes/models.py:24
             ActivateModelRequest -> ActiveModelResponse
  [MODIFIED] GET  /status           -> backend/app/api/routes/status.py:18
             added field: rows_failed (int)
  [REMOVED]  (none)

Full current surface (8 endpoints):
  GET  /health           health.py   -> HealthResponse
  POST /train            train.py    -> TrainAcceptedResponse (202)
  GET  /status           status.py   -> StatusResponse
  POST /predict          predict.py  -> PredictResponse
  GET  /metrics          metrics.py  -> MetricsResponse
  GET  /models           models.py   -> ModelListResponse
  POST /models/activate  models.py   -> ActiveModelResponse
  GET  /                 main.py     -> service banner

Contract impact: docs/API_CONTRACT.md   [UPDATED | NO CHANGE NEEDED]
Frontend impact: BREAKING — /status response gained a required field | none
=== END REPORT ===
```

Rules:
- Build the "full current surface" by actually reading the router files each time. Never from memory.
- If a request or response **shape** changed, flag it explicitly as breaking for the UI owner.
- If you added an endpoint not in `docs/API_CONTRACT.md`, update that doc **in the same run** and
  say that you did.

---

## 3. Target repository structure

Scaffold exactly this. Create empty-but-real files with docstrings rather than leaving gaps —
a missing file is an invitation for someone to invent their own location for it.

```
passione/
├── CLAUDE.md                      # this file
├── README.md                      # what it is, how to run it (Passioné branding)
├── REPORT.md                      # graded write-up, filled at the end
├── docker-compose.yml             # ONE command brings up api + ui
├── .env.example                   # every env var, no real values
├── .gitignore
├── Makefile                       # make up / make test / make train / make freeze
│
├── docs/
│   ├── API_CONTRACT.md            # source of truth shared with the UI owner
│   ├── INTEGRATION.md             # the two seams: ML→backend, backend→UI
│   └── ARCHITECTURE.md            # diagram + why the pipeline is decoupled
│
├── backend/                       # ← MINE. Everything below is the main work.
│   ├── Dockerfile
│   ├── requirements.txt           # PINNED
│   ├── requirements-dev.txt
│   └── app/
│       ├── main.py                # app factory, CORS, lifespan, error handlers
│       ├── api/
│       │   ├── router.py          # single place all routers are included
│       │   └── routes/
│       │       ├── health.py      # GET  /health
│       │       ├── train.py       # POST /train
│       │       ├── status.py      # GET  /status
│       │       ├── predict.py     # POST /predict
│       │       ├── metrics.py     # GET  /metrics
│       │       └── models.py      # GET  /models, POST /models/activate
│       ├── schemas/               # Pydantic v2 only — no raw dicts cross the boundary
│       │   ├── common.py          # ErrorEnvelope
│       │   ├── health.py
│       │   ├── train.py
│       │   ├── status.py
│       │   ├── predict.py
│       │   ├── metrics.py
│       │   └── models.py          # GET /models, POST /models/activate shapes
│       ├── services/              # all business logic
│       │   ├── job_manager.py     # in-memory job registry, real row counts
│       │   ├── training_service.py# CSV parsing/validation; persists uploads for mlcore.train_model
│       │   ├── prediction_service.py # grounding decision lives HERE, not in the route
│       │   └── enrichment.py      # TMDB client: retries, timeout, graceful fallback
│       ├── ml_adapter/            # the ONLY thing that imports mlcore
│       │   └── mlcore_client.py   # wraps mlcore's six functions; applies our thresholds
│       └── core/
│           ├── config.py          # pydantic-settings — the ONLY place env is read
│           ├── errors.py          # AppError hierarchy + handlers
│           └── logging.py
│
├── ml/                             # ← TEAMMATE A. Not mine. See docs/INTEGRATION.md.
│   ├── pyproject.toml              # installable package: `pip install -e ./ml`
│   ├── requirements.txt            # PINNED (empty until real training deps land)
│   └── mlcore/
│       ├── __init__.py
│       └── api.py                  # the frozen interface — six functions, nothing else
│
├── frontend/                      # ← TEAMMATE B. Minimal, working, replaceable.
│   ├── index.html                 # one page: form → score → metrics
│   ├── app.js                     # fetch only; zero logic
│   ├── styles.css
│   └── Dockerfile                 # static serve
│
├── models/                        # artifacts. gitignored except .gitkeep
├── data/                          # datasets. gitignored except .gitkeep + samples/
│   └── samples/                   # tiny committed fixtures: clean_50.csv, broken.csv
├── tests/
│   ├── fixtures/                  # predict_ok.json, predict_unseen.json, empty.csv, header_only.csv
│   ├── test_contract.py           # response shapes match docs/API_CONTRACT.md
│   ├── test_hostile_input.py      # the five hostile cases below
│   └── test_reproducibility.py    # two runs, same seed, identical metrics
├── scripts/
│   └── smoke.sh                   # curl every endpoint in order, exit non-zero on failure
└── .github/
    ├── CODEOWNERS                 # backend/* me, ml/* A, frontend/* B
    └── workflows/ci.yml           # lint + tests on PR
```

---

## 4. The two integration seams

```
frontend/  ──HTTP + JSON──▶  backend/  ──frozen Python import──▶  ml/
             API_CONTRACT.md              mlcore.api
```

### Seam 1 — mlcore import

`ml/` ships an installable package, `mlcore`, exposing exactly six functions from `mlcore/api.py`:
`health_check`, `load_model`, `get_model_metadata`, `predict`, `predict_batch`, `train_model`.
`backend/app/ml_adapter/mlcore_client.py` is the **only** file in `backend/` that imports it —
routes and services call the adapter, never `mlcore` directly.

**These six signatures and their return shapes are specified and frozen in `docs/INTEGRATION.md`.
Read it before writing or changing anything in `mlcore_client.py`, and treat the signatures as
fixed.** It is a negotiated contract with the ML owner, not something to adjust unilaterally — if
the adapter cannot work with the shape as written, stop and tell me rather than changing either
side.

`mlcore_client.py` never trusts that mlcore "never raises": every one of the six calls is wrapped
in try/except, and an unexpected exception degrades to the same `grounded: false` /
`status: degraded` shape a normal ungrounded response would produce.

The ownership split is strict: **mlcore owns prediction semantics** — `grounded`,
`predicted_label`, and `reason` pass through from `predict()` unmodified, no backend
recomputation, no confidence threshold on our side. **The backend owns service readiness only**,
via `MIN_ROC_AUC` — it gates `/health`'s status and gates whether `/predict` is attempted at all.
If the service isn't ready, the backend returns `MODEL_NOT_READY` (409) before calling
`mlcore.predict()`, rather than calling it and second-guessing the result.

Until `mlcore`'s internals are real, they return dummy, contract-shaped, `grounded: false`
responses: `/health` reports `degraded` with `model_loaded: false`, and `/predict` returns
`grounded: false`. **It never fabricates a score.** Swapping in real training/inference logic
changes nothing outside `ml/` — the six signatures don't move.

### Seam 2 — backend → UI

- The UI holds no logic: it POSTs `/predict`, GETs `/status` and `/metrics`, renders JSON.
- `CORS_ORIGINS` comes from env. Never hardcode an origin.
- **Additive changes only** during the build window. New optional response fields are safe; renaming
  or removing a field is not. If a break is unavoidable, announce it in the API surface report.
- The UI must render the *ungrounded* case as prominently as the grounded one. A blank box where a
  score should be is a bug; "we can't confidently score this, here's why" is correct behaviour.

---

## 5. The API contract

Base URL `http://localhost:8000`. Every error uses one envelope:

```json
{ "error": { "code": "MODEL_NOT_READY", "message": "No trained model is loaded.", "detail": null } }
```
Codes: `VALIDATION_ERROR` 422 · `MODEL_NOT_READY` 409 · `JOB_NOT_FOUND` 404 · `EMPTY_DATASET` 400 ·
`BAD_CSV` 400.

**GET /health**
```json
{ "status": "ok", "model_loaded": true, "model_version": "rf_v3", "enrichment_api_connected": true }
```
`status` is `"ok"` **only** when a trained model is loaded *and* its metrics cleared `MIN_ROC_AUC`.
Otherwise `"degraded"`. A started container is not a ready service.

**POST /train** — multipart only: `file=<csv>` (required) + `random_seed` form field (default `42`).
No JSON-body mode — see docs/API_CONTRACT.md for why an earlier `csv_path` JSON mode was dropped
rather than fixed.
```json
{ "job_id": "t3f1", "rows_received": 5000, "status": "queued" }   // 202
```

**GET /status?job_id=t3f1**
```json
{ "job_id": "t3f1", "status": "training", "rows_total": 5000, "rows_processed": 3200,
  "rows_failed": 4, "message": null, "metrics": null, "model_version": null }
```
`queued | training | complete | failed`. Real counts, never hardcoded. `complete` only when
`rows_processed + rows_failed == rows_total`. A crash sets `failed` — never leave it saying
`training` forever.

**POST /predict**
```json
{ "title": "Midnight Run", "genre": "Thriller", "duration_minutes": 24,
  "upload_time": "2026-08-06T18:30:00Z", "language": "en",
  "tags": ["suspense", "indie", "short-film"] }
```
Readiness is checked before mlcore is called at all: if no model is loaded or its `roc_auc` hasn't
cleared `MIN_ROC_AUC`, this returns `MODEL_NOT_READY` (409) immediately — `mlcore.predict()` is
never invoked. Once the service is ready, mlcore's answer passes through unmodified:
```json
{ "trending_probability": 0.71, "predicted_label": "trending", "model_version": "rf_v3",
  "top_features": ["genre=Thriller", "upload_hour=18", "tag_count=3"],
  "grounded": true, "reason": null }
```
Ungrounded — service is ready, but mlcore itself reports an unseen category or low confidence for
this specific input. `grounded`, `predicted_label`, and `reason` are mlcore's own decision, never
re-derived by the backend:
```json
{ "trending_probability": null, "predicted_label": "unknown", "model_version": "rf_v3",
  "top_features": [], "grounded": false,
  "reason": "Unseen genre 'Kuchipudi-Fusion' — no fallback encoding." }
```

**GET /metrics** — last run's held-out evaluation, read straight from `metrics_v{N}.json`:
`model_version, precision, recall, f1, roc_auc, accuracy, positive_rate, random_seed,
split {train,val,test}, trained_at`.

**GET /models** → `{"active": "rf_v3", "available": ["rf_v3","rf_v2","logreg_v1"]}`
**POST /models/activate** `{"model_version": "rf_v2"}` → `{"active": "rf_v2"}` — so a bad retrain
rolls back without retraining.

Mirror all of this into `docs/API_CONTRACT.md` with a change-log table at the bottom, and append a
row whenever it changes.

---

## 6. Backend conventions

- **FastAPI + Pydantic v2.** Every request and response is a schema class in `app/schemas/`. No raw
  dicts cross the API boundary.
- **Routes are thin.** Validate → call one service → return a schema. If a route body passes ~15
  lines, the logic belongs in a service. The grounding decision in particular lives in
  `prediction_service.py`, never in `routes/predict.py`.
- **Config only through `core/config.py`.** No `os.getenv` anywhere else.
- **Errors only through `core/errors.py`.** One exception handler, one envelope, no traceback ever
  reaches a client.
- **Training runs in a background task.** `/train` returns 202 immediately; `/status` is the only
  way to learn progress. Row-level failures increment `rows_failed` and are logged with the row
  index — they never abort the run.
- **Enrichment is optional and always fallback-safe.** `httpx.AsyncClient`, explicit timeout, capped
  retries; on failure log once and continue with metadata-only features. A slow TMDB call must never
  block or fail `/predict`.
- **Model loading and readiness are owned by `ml_adapter/mlcore_client.py`.** It calls
  `mlcore.health_check()` / `get_model_metadata()`, checks the reported `roc_auc` against
  `MIN_ROC_AUC`, and exposes translated `HealthResponse`/`MetricsResponse`/`ModelListResponse`
  objects — no other module re-derives readiness. mlcore itself owns discovery and version
  selection; the backend never lists artifacts off disk. `GET /models`'s `available` list can only
  ever reflect the one currently-loaded version, since the frozen interface has no "list all
  versions" call.
- Type hints everywhere. `async def` for I/O-bound handlers.

---

## 7. Hard requirements — check these before calling any task done

1. `docker compose up` brings up api + ui with **zero manual steps**.
2. Raw metadata reaches the model **only** through the versioned feature pipeline — never a raw
   unencoded field.
3. Every training run fixes its seed and records its exact split. **Two runs on the same dataset and
   seed produce identical metrics.** Zero partial credit on this one — `tests/test_reproducibility.py`
   must actually assert it.
4. `/health` is not-ok until a real trained model is loaded and passes the metric bar.
5. `/status` reports real counts including `rows_failed`.
6. `/predict` always returns `model_version` and `grounded`.
7. Unconfident or unseen input → `grounded: false` with a plain-language `reason`. Never guess.
8. **All dependencies pinned.** No `latest`, ever.
9. Containers run as a **non-root** user.
10. API keys come from env vars only — never in a Dockerfile line, never in source, never in git.
    If you ever see a key in a diff, stop and tell me.

**Hostile input** — each must return a clean 4xx with the error envelope, never a stack trace or a
dead container. Cover all five in `tests/test_hostile_input.py`:
empty training CSV · CSV with a header row and zero data rows · `/predict` missing a required field ·
`/predict` with a genre or language never seen in training · `/predict` sent before any model is trained.

---

## 8. Build order — pipe before model

The single most common way to fail this is a clever model at 7:40 and no working endpoint. Build the
plumbing with fake logic first, then replace the dummies one at a time. From that moment on, every
minute improves something that already works.

1. **Skeleton.** `docker compose up` runs ui → api. `/train` writes a dummy metrics file and returns
   a fake `job_id`; `/status` returns hardcoded `complete`; `/predict` returns a canned score with
   `grounded: false`; `/health` returns `degraded`. End to end, no real logic.
2. **Real UI wiring.** A metadata record can be submitted, previewed, and a response rendered.
3. **Real training.** Rows genuinely produce a model artifact and held-out metrics.
4. **Honest `/status` and `/health`.** Real counts; readiness gated on loaded model + metric bar.
5. **Real predictions.** Grounded scores, `top_features`, metrics shown alongside.
6. **Hardening.** Non-root, pinned deps, hostile-input tests, `scripts/smoke.sh` green.
7. **Freeze and report.**

Keep the feature set boring — genre, duration, upload-hour/day-of-week, language, tag count is
enough. Enrich only after everything above works, and keep the boring set as the fallback.

---

## 9. Git workflow

- `main` is protected and must always run. No direct pushes.
- Branches: `backend/<thing>`, `ml/<thing>`, `ui/<thing>`.
- Commits: `backend: add real row counting to /status`. Small and frequent.
- Before suggesting a commit, confirm nothing under `data/`, `models/`, or `.env` is staged.
- Never edit `ml/` or `frontend/` without telling me first which file and why.
- Near the build freeze, prefer committing working code over finishing a refactor. Work that is not
  committed does not exist.

---

## 10. How to work with me

- If a task needs a decision I haven't made (label definition, imbalance strategy, model type), ask —
  the report is graded on whether we *chose* rather than *defaulted*, so I need to answer these.
- Tell me when a change makes `REPORT.md` stale: the methods table, the results table, or the
  limitations section.
- Prefer the simple thing that works. Model cleverness is worth 10 marks out of 100; engineering and
  reasoning are worth 90.
- Don't tell me something works if you haven't run it. If you couldn't run it, say so.
- **And end every backend execution with the API surface report from section 2.**
