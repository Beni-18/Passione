# INTEGRATION.md — how the pieces plug together

Three people, three directories, two seams. **Neither seam is a file-on-disk handoff.**

```
frontend/  ──HTTP + JSON──▶  backend/  ──frozen Python import──▶  ml/
             API_CONTRACT.md              mlcore.api
   (UI)          (API)                    (training)
```

| Directory | Owner | Talks to the rest of the repo via |
|---|---|---|
| `frontend/` | UI owner | HTTP calls described in `docs/API_CONTRACT.md` |
| `backend/` | Backend owner | both seams |
| `ml/` | ML owner | the six functions in `mlcore/api.py` — nothing else |

---

## Seam 1 — mlcore → backend (frozen import, not a file handoff)

**Superseded:** earlier drafts of this doc specified a `models/model_v{N}.joblib` +
`metrics_v{N}.json` file handoff read directly off disk. **That's no longer how this works.** The
`models/` and `data/` directories still exist for artifacts mlcore may write internally, but the
backend does not read them directly, and there is no joblib bundle the backend loads itself.

**For the ML owner. This section is the entire interface.** `ml/` ships an installable package,
`mlcore`, exposing exactly six functions from `mlcore/api.py`:

```python
from mlcore.api import (
    health_check, load_model, get_model_metadata,
    predict, predict_batch, train_model,
)
```

These six signatures and their return shapes are **frozen as of M0**. Everything else inside
`mlcore` is free to change — swap algorithms, restructure internals, add helper modules — as long
as these six keep working and returning the same shape. All six currently return dummy,
contract-shaped, `grounded: false` / zero-row responses (build order step 1 — pipe before model).
Internals get swapped for real implementations at M3/M4 without touching these signatures.

You never import backend code and the backend never imports `mlcore` outside of
`backend/app/ml_adapter/mlcore_client.py`.

### The five rules

1. **`backend/app/ml_adapter/mlcore_client.py` is the only file in `backend/` that imports
   `mlcore`.** Routes and services never import it directly — they call the adapter, which
   translates `mlcore`'s dicts into our Pydantic schemas (`PredictResponse`, `StatusResponse`,
   etc.) and applies our grounding/readiness policy (`MIN_ROC_AUC`, `GROUNDING_MIN_CONFIDENCE`) on
   top of whatever `mlcore` reports. `mlcore` doesn't know about our thresholds — a `grounded: true`
   or `passed_gate: true` claim from `mlcore` is not the final word; the adapter's threshold check
   is.

2. **The adapter never trusts "never raises."** Every `mlcore` call is wrapped in try/except in
   `mlcore_client.py`. An unexpected exception becomes `grounded: false` / `status: degraded`, the
   same shape a normal ungrounded response would produce — never a 500.

3. **`ml/requirements.txt` and `backend/requirements.txt` must be dependency-compatible** — same
   interpreter, same environment (the backend's Docker image installs both, plus `mlcore` itself,
   in one build — see `backend/Dockerfile`). Pin both. If versions conflict, that's a blocking issue
   to raise with the backend owner immediately, not something to work around silently.

4. **`train_model`'s `progress_cb`** is how `POST /status` gets real row counts during a background
   training run. The backend passes a callback that writes into `job_manager`; `mlcore` calls it
   with `(processed, failed, total, status)` at whatever cadence it likes during the fit. The
   backend only trusts a non-zero `total` from the callback — it keeps its own upload-time row
   count until `mlcore` reports a real one, so the dummy stage's `progress_cb(0, 0, 0, "complete")`
   doesn't stomp on an accurate count taken from the uploaded CSV.

5. **`predict`/`predict_batch` take our raw `/predict` field names as a dict** — no feature
   engineering happens on the backend side; that's entirely inside `mlcore`. The dict keys are
   exactly `title, genre, duration_minutes, upload_time, language, tags`.

### The six functions, what they return, and what the backend does with each

| Function | Called from | Backend behavior |
|---|---|---|
| `health_check() -> dict` | `GET /health` | Adapter checks `model_loaded` and `roc_auc >= MIN_ROC_AUC` before reporting `status: "ok"`. |
| `get_model_metadata() -> dict` | `GET /metrics`, `GET /models` | Adapter re-checks `passed_gate` and `roc_auc` against `MIN_ROC_AUC` independently of mlcore's own `passed_gate` flag. `GET /models`'s `available` list can only ever contain the one currently-loaded version — there is no "list all versions" function among the six, so real version history isn't exposed through this seam. |
| `load_model(version) -> dict` | `POST /models/activate` | If `loaded` is false, the backend returns `MODEL_NOT_READY` (409), not a 500. |
| `predict(metadata: dict) -> dict` | `POST /predict` | Adapter re-checks `confidence >= GROUNDING_MIN_CONFIDENCE` and forces `grounded: false` if mlcore's own `grounded: true` doesn't clear it. Any non-empty `errors` list from mlcore also forces `grounded: false`. |
| `predict_batch(items: list[dict]) -> list[dict]` | *(not currently wired to a route — no batch endpoint in the API contract yet)* | Wrapped and available in `mlcore_client.py` for when/if a batch endpoint is added. |
| `train_model(csv_path, progress_cb, seed, algo) -> dict` | `POST /train`'s background task | Backend writes a multipart upload to disk first (`training_service.persist_uploaded_csv`) since this function takes a path, not bytes. |

### Field-mapping note (why response field names don't match 1:1)

`mlcore`'s dicts carry fields our API contract doesn't expose (`confidence`, `confidence_band`,
`predicted_label_display`, `errors`, `unknown_fields`) and use different vocabulary in places
(`predicted_label: "uncertain"` vs. our `"unknown"`). The adapter maps every field explicitly by
name in `mlcore_client.py` — it does not rename our schemas to match mlcore's keys, and it does not
forward mlcore's extra fields to the API. If `mlcore`'s shape gains something the API contract
should surface, that's a contract change to raise explicitly, not a silent pass-through.

### Testing your changes against the backend

```bash
pip install -e ./ml                                        # from repo root
docker compose up --build                                   # backend now imports mlcore
curl localhost:8000/health                                  # model_loaded should flip to true once mlcore reports it
curl localhost:8000/metrics                                 # should reflect get_model_metadata()'s metrics dict
curl -X POST localhost:8000/predict -H 'content-type: application/json' \
     -d @tests/fixtures/predict_ok.json                     # grounded: true once mlcore + our thresholds agree
curl -X POST localhost:8000/predict -H 'content-type: application/json' \
     -d @tests/fixtures/predict_unseen.json                 # grounded: false, with a reason
```

If a call to any of the six functions raises where you expected a normal dict, check
`mlcore_client.py`'s logs — the adapter catches the exception and degrades gracefully, but it also
logs it, so a real bug in `mlcore` won't be silently invisible.

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

If either seam turns out to be wrong — `mlcore`'s six-function shape can't carry something the
model needs, or the UI needs a shape the contract doesn't have — **raise it as a change, don't work
around it.** A private workaround on one side of a seam is how a working system becomes an
unworkable one at 7pm.
