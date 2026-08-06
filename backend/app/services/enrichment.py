"""TMDB client: retries, timeout, graceful fallback.

Optional and always fallback-safe — a slow or failing TMDB call must never
block or fail /predict. On any error this logs once and returns None so the
caller continues with metadata-only features. Does NOT get called anywhere
yet in phase 1; wired in once real feature enrichment is decided (section 10
open question: live TMDB vs metadata-only for the build window).
"""
from __future__ import annotations

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def fetch_enrichment(title: str) -> dict | None:
    """Best-effort TMDB lookup for `title`. Returns None on any failure.

    Never raises: timeout, non-2xx, and connection errors are all caught
    and logged once, then treated identically as "no enrichment available".
    """
    if not settings.enrichment_enabled or not settings.tmdb_api_key:
        return None

    async with httpx.AsyncClient(timeout=settings.tmdb_timeout_seconds) as client:
        for attempt in range(settings.tmdb_max_retries + 1):
            try:
                response = await client.get(
                    f"{settings.tmdb_base_url}/search/movie",
                    params={"query": title, "api_key": settings.tmdb_api_key},
                )
                response.raise_for_status()
                return response.json()
            except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.TransportError) as exc:
                if attempt == settings.tmdb_max_retries:
                    logger.warning("TMDB enrichment failed for %r after retries: %s", title, exc)
                    return None
    return None


async def is_enrichment_api_connected() -> bool:
    """Cheap reachability check used by GET /health. Never raises."""
    if not settings.enrichment_enabled or not settings.tmdb_api_key:
        return False
    try:
        async with httpx.AsyncClient(timeout=settings.tmdb_timeout_seconds) as client:
            response = await client.get(f"{settings.tmdb_base_url}/configuration",
                                         params={"api_key": settings.tmdb_api_key})
            return response.status_code == 200
    except (httpx.TimeoutException, httpx.TransportError):
        return False
