"""Real httpx-backed enrichment client — mocked at the transport level
(httpx.MockTransport, no extra test dependency needed) so no real network
call happens. Covers the four failure modes that must all degrade to
None/False rather than raise: success (control case), timeout, 429
rate-limiting, and a malformed (non-JSON) response body.
"""
from __future__ import annotations

import httpx
import pytest

from app.core.config import settings
from app.services import enrichment

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def _enrichment_enabled(monkeypatch):
    monkeypatch.setattr(settings, "enrichment_enabled", True)
    monkeypatch.setattr(settings, "tmdb_api_key", "test-key")
    monkeypatch.setattr(settings, "enrichment_max_retries", 1)  # keep retry-path tests fast


def _patch_transport(monkeypatch, handler):
    class _MockClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(handler)
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", _MockClient)


async def test_fetch_enrichment_success(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": [{"title": "Midnight Run"}]})

    _patch_transport(monkeypatch, handler)

    result = await enrichment.fetch_enrichment("Midnight Run")
    assert result == {"results": [{"title": "Midnight Run"}]}


async def test_fetch_enrichment_timeout_falls_back_to_none(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("simulated timeout", request=request)

    _patch_transport(monkeypatch, handler)

    result = await enrichment.fetch_enrichment("Midnight Run")
    assert result is None


async def test_fetch_enrichment_rate_limited_falls_back_to_none(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"status_message": "rate limited"})

    _patch_transport(monkeypatch, handler)

    result = await enrichment.fetch_enrichment("Midnight Run")
    assert result is None


async def test_fetch_enrichment_malformed_response_falls_back_to_none(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not valid json{{{")

    _patch_transport(monkeypatch, handler)

    result = await enrichment.fetch_enrichment("Midnight Run")
    assert result is None


async def test_fetch_enrichment_network_error_falls_back_to_none(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("simulated connection failure", request=request)

    _patch_transport(monkeypatch, handler)

    result = await enrichment.fetch_enrichment("Midnight Run")
    assert result is None


async def test_fetch_enrichment_disabled_never_calls_network(monkeypatch):
    monkeypatch.setattr(settings, "enrichment_enabled", False)

    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("network should never be reached when enrichment is disabled")

    _patch_transport(monkeypatch, handler)

    result = await enrichment.fetch_enrichment("Midnight Run")
    assert result is None


async def test_fetch_enrichment_no_api_key_never_calls_network(monkeypatch):
    monkeypatch.setattr(settings, "tmdb_api_key", None)

    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("network should never be reached with no API key")

    _patch_transport(monkeypatch, handler)

    result = await enrichment.fetch_enrichment("Midnight Run")
    assert result is None


async def test_is_enrichment_api_connected_true_on_success(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"images": {}})

    _patch_transport(monkeypatch, handler)

    assert await enrichment.is_enrichment_api_connected() is True


async def test_is_enrichment_api_connected_false_on_failure(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "server error"})

    _patch_transport(monkeypatch, handler)

    assert await enrichment.is_enrichment_api_connected() is False


async def test_fetch_enrichment_retries_before_giving_up(monkeypatch):
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(503, json={"status_message": "temporarily unavailable"})

    _patch_transport(monkeypatch, handler)
    monkeypatch.setattr(settings, "enrichment_max_retries", 2)

    result = await enrichment.fetch_enrichment("Midnight Run")
    assert result is None
    assert calls["count"] == 3  # initial attempt + 2 retries


async def test_fetch_enrichment_recovers_after_transient_failure(monkeypatch):
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(503, json={"status_message": "temporarily unavailable"})
        return httpx.Response(200, json={"results": []})

    _patch_transport(monkeypatch, handler)

    result = await enrichment.fetch_enrichment("Midnight Run")
    assert result == {"results": []}
    assert calls["count"] == 2
