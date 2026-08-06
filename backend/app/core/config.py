"""The only place environment variables are read.

Every other module that needs a configurable value imports `settings` from here
instead of calling `os.getenv` directly. This keeps env access auditable in one
file and lets tests override settings by constructing a `Settings()` with kwargs.

Does NOT validate that referenced paths (models/, data/) exist — that is
`model_registry.py`'s and `training_service.py`'s job at call time.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Passioné"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # CORS — never hardcode an origin in route/app code, only read it here.
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:8080"]

    # Filesystem locations for the ML → backend seam (docs/INTEGRATION.md).
    models_dir: str = "models"
    data_dir: str = "data"

    # Readiness gate: /health is only "ok" once the active model's roc_auc
    # clears this bar. Below it the model is "trained" but not "ready".
    # Also gates whether /predict is attempted at all — see
    # ml_adapter/mlcore_client.py. Grounding itself (whether a specific
    # prediction is trustworthy) is mlcore's call, not a backend threshold.
    min_roc_auc: float = 0.65

    # Enrichment (TMDB). Optional and always fallback-safe — see enrichment.py.
    # tmdb_api_key/tmdb_base_url are provider-specific; the timeout/retry/
    # enabled knobs are enrichment-feature-level, not TMDB-specific, hence
    # the different prefix.
    tmdb_api_key: str | None = None
    tmdb_base_url: str = "https://api.themoviedb.org/3"
    enrichment_timeout_seconds: float = 3.0
    enrichment_max_retries: int = 2
    enrichment_enabled: bool = False


settings = Settings()
