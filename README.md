# Passioné

Passioné takes the metadata of a newly uploaded movie or short film — genre, duration, upload
time, language, tags — and returns a trending-likelihood score, backed by honest evaluation
metrics rather than a bare number.

## Run it

```bash
cp .env.example .env   # optional — defaults work without it
docker compose up
```

This brings up:
- **api** on `http://localhost:8000` (FastAPI backend)
- **ui** on `http://localhost:8080` (static frontend)

No model is trained yet on a fresh checkout, so `/health` reports `"degraded"` and `/predict`
returns `grounded: false` — this is correct behaviour, not a bug. See
[docs/API_CONTRACT.md](docs/API_CONTRACT.md) for the full request/response shapes and
[docs/INTEGRATION.md](docs/INTEGRATION.md) for how a trained model gets picked up.

## Repository layout

| Directory | Owner | Purpose |
|---|---|---|
| `backend/` | Backend | FastAPI service — the only thing this README's owner maintains directly |
| `ml/` | ML | Training code; hands off two files into `models/` |
| `frontend/` | UI | Minimal static page — form, score, metrics |

## Useful commands

```bash
make up      # docker compose up --build
make test    # run the backend test suite
make train   # train a model from data/samples/clean_50.csv
make freeze  # tests + scripts/smoke.sh — the pre-submission checklist
```

See [CLAUDE.md](CLAUDE.md) for the full engineering spec and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
for why the pipeline is split this way.
