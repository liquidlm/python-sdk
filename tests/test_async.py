"""Async client behavior; mirrors the sync contract."""

from __future__ import annotations

import httpx
import pytest

from liquidlm import AsyncLiquidLM, NotFoundError


def make_client(handler, **kwargs) -> AsyncLiquidLM:
    transport = httpx.MockTransport(handler)
    return AsyncLiquidLM(
        "https://api.example.test", token="synthetic-token", transport=transport, **kwargs
    )


async def test_async_query_and_headers() -> None:
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"results": [{"id": "1"}]})

    async with make_client(handler) as client:
        result = await client.search_hybrid("notes")
    assert seen["method"] == "QUERY"
    assert seen["auth"] == "Bearer synthetic-token"
    assert result["results"] == [{"id": "1"}]


async def test_async_error_mapping() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"internal": "detail"})

    async with make_client(handler, max_read_retries=0) as client:
        with pytest.raises(NotFoundError):
            await client.get_knowledge("missing")


async def test_async_pagination() -> None:
    pages = [
        {"items": [{"id": "1"}], "total": 2, "hasMore": True},
        {"items": [{"id": "2"}], "total": 2, "hasMore": False},
    ]
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(200, json=pages[calls["count"] - 1])

    async with make_client(handler) as client:
        items = [item async for item in client.list_knowledge(limit=1)]
    assert [i["id"] for i in items] == ["1", "2"]


async def test_async_sse() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, text="data: one\n\ndata: two\n\n", headers={"content-type": "text/event-stream"}
        )

    async with make_client(handler) as client:
        payloads = [
            p async for p in client.stream_sse("POST", "/chat/sessions/s/completions", json={})
        ]
    assert payloads == ["one", "two"]
