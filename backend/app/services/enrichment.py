"""TMDB client: retries with backoff, timeout, graceful fallback.

Optional and always fallback-safe — a slow or failing TMDB call must never
block or fail /predict. On any failure (timeout, non-2xx, network error, or
a malformed/non-JSON response body) this logs once and returns None, so the
caller always continues with metadata-only features rather than raising.

Gated entirely behind `settings.enrichment_enabled` (currently False — see
REPORT.md's "metadata-only for the build window" decision). `fetch_enrichment`
is real and tested but has no caller yet beyond this module itself;
`is_enrichment_api_connected` is called from routes/health.py. Wiring
`fetch_enrichment`'s output into the /predict payload is a separate decision
— mlcore's predict() takes exactly the six frozen `/predict` fields
(docs/INTEGRATION.md Seam 1, rule 5), so adding enrichment data to that
payload would mean widening the contract with the ML owner, not something to
do unilaterally here.
"""
from __future__ import annotations

import asyncio
import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# Failure modes worth retrying: transient network issues, timeouts, and any
# non-2xx status (including 429 rate-limiting). A malformed response body is
# NOT retried — the request succeeded, the payload just isn't usable JSON,
# so retrying identical inputs would just reproduce the same bad response.
_RETRYABLE_EXCEPTIONS = (httpx.TimeoutException, httpx.HTTPStatusError, httpx.TransportError)


async def _get_with_retries(client: httpx.AsyncClient, url: str, params: dict, context: str) -> dict | None:
    """Shared GET-with-retries-and-backoff helper. Never raises.

    Returns the parsed JSON body on success, or None after exhausting
    retries or hitting a response body that isn't valid JSON.
    """
    max_retries = settings.enrichment_max_retries
    for attempt in range(max_retries + 1):
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
        except _RETRYABLE_EXCEPTIONS as exc:
            if attempt == max_retries:
                logger.warning("%s failed after %d retries: %s", context, max_retries, exc)
                return None
            # Exponential backoff so a rate-limited (429) or flaky endpoint
            # isn't hammered with immediate back-to-back retries.
            await asyncio.sleep(0.1 * (2**attempt))
            continue

        try:
            return response.json()
        except ValueError as exc:
            # response.json() raises a plain ValueError (json.JSONDecodeError)
            # on a malformed body — httpx's own exception types above don't
            # cover this, so it needs its own catch. The request succeeded;
            # retrying won't fix a malformed body, so fail immediately.
            logger.warning("%s returned a malformed (non-JSON) response: %s", context, exc)
            return None

    return None


async def fetch_enrichment(title: str) -> dict | None:
    """Best-effort TMDB lookup for `title`. Returns None on any failure or
    if enrichment is disabled/unconfigured.
    """
    if not settings.enrichment_enabled or not settings.tmdb_api_key:
        return None

    async with httpx.AsyncClient(timeout=settings.enrichment_timeout_seconds) as client:
        return await _get_with_retries(
            client,
            f"{settings.tmdb_base_url}/search/movie",
            {"query": title, "api_key": settings.tmdb_api_key},
            context=f"TMDB enrichment lookup for {title!r}",
        )


async def is_enrichment_api_connected() -> bool:
    """Cheap reachability check used by GET /health. Never raises."""
    if not settings.enrichment_enabled or not settings.tmdb_api_key:
        return False

    async with httpx.AsyncClient(timeout=settings.enrichment_timeout_seconds) as client:
        result = await _get_with_retries(
            client,
            f"{settings.tmdb_base_url}/configuration",
            {"api_key": settings.tmdb_api_key},
            context="TMDB reachability check",
        )
        return result is not None
