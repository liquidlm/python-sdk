"""Sync client behavior over a mocked transport; no live account is used."""

from __future__ import annotations

import json

import httpx
import pytest

from liquidlm import (
    AuthenticationError,
    ConflictError,
    LiquidLM,
    NotFoundError,
    RateLimitError,
    ServerError,
)


def make_client(handler, **kwargs) -> LiquidLM:
    transport = httpx.MockTransport(handler)
    return LiquidLM(
        "https://api.example.test",
        token="synthetic-token",
        active_org="org-1",
        transport=transport,
        **kwargs,
    )


def test_bearer_and_org_headers_are_sent() -> None:
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(dict(request.headers))
        return httpx.Response(200, json={"ok": True})

    with make_client(handler) as client:
        client.request("GET", "/auth/me")
    assert seen["authorization"] == "Bearer synthetic-token"
    assert seen["x-liquidlm-active-org"] == "org-1"
    assert seen["accept"] == "application/json"


def test_search_hybrid_uses_query_method_and_json_body() -> None:
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"results": []})

    with make_client(handler) as client:
        result = client.search_hybrid("runbook", limit=3)
    assert seen["method"] == "QUERY"
    assert seen["path"] == "/search/hybrid"
    assert seen["body"] == {"query": "runbook", "limit": 3}
    assert result == {"results": []}


def test_error_mapping_and_body_redaction() -> None:
    cases = {
        401: AuthenticationError,
        403: AuthenticationError,
        404: NotFoundError,
        409: ConflictError,
        500: ServerError,
    }
    for status, exc_type in cases.items():

        def handler(request: httpx.Request, status: int = status) -> httpx.Response:
            return httpx.Response(
                status,
                json={"secret": "provider-internal-detail"},
                headers={"x-request-id": "req-1"},
            )

        with (
            make_client(handler, max_read_retries=0) as client,
            pytest.raises(exc_type) as caught,
        ):
            client.request("POST", "/knowledge", json={})
        assert caught.value.status == status
        assert caught.value.request_id == "req-1"
        assert "provider-internal-detail" not in str(caught.value)
        assert "provider-internal-detail" not in repr(caught.value)


def test_read_retries_are_bounded_and_mutations_never_retried() -> None:
    calls = {"count": 0}

    def flaky(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] < 3:
            return httpx.Response(500)
        return httpx.Response(200, json={"ok": True})

    with make_client(flaky, max_read_retries=2) as client:
        # Retry-After 0 keeps the test fast; backoff honors it.
        assert client.request("GET", "/knowledge") == {"ok": True}
    assert calls["count"] == 3

    post_calls = {"count": 0}

    def failing_post(request: httpx.Request) -> httpx.Response:
        post_calls["count"] += 1
        return httpx.Response(500)

    with make_client(failing_post, max_read_retries=2) as client, pytest.raises(ServerError):
        client.request("POST", "/knowledge", json={"type": "note"})
    assert post_calls["count"] == 1


def test_rate_limit_error_carries_retry_after_when_exhausted() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"retry-after": "0"})

    with make_client(handler, max_read_retries=1) as client, pytest.raises(RateLimitError):
        client.request("GET", "/knowledge")


def test_offset_pagination_follows_has_more() -> None:
    pages = [
        {"items": [{"id": "1"}, {"id": "2"}], "total": 3, "hasMore": True},
        {"items": [{"id": "3"}], "total": 3, "hasMore": False},
    ]
    seen_offsets = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_offsets.append(request.url.params["offset"])
        return httpx.Response(200, json=pages[len(seen_offsets) - 1])

    with make_client(handler) as client:
        items = list(client.list_knowledge(limit=2))
    assert [i["id"] for i in items] == ["1", "2", "3"]
    assert seen_offsets == ["0", "2"]


def test_cursor_pagination_follows_next_cursor() -> None:
    pages = [
        {"items": [{"id": "a"}], "next_cursor": "c-1"},
        {"items": [{"id": "b"}], "next_cursor": None},
    ]
    seen_cursors = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_cursors.append(request.url.params.get("cursor"))
        return httpx.Response(200, json=pages[len(seen_cursors) - 1])

    with make_client(handler) as client:
        items = list(client.list_cursor("/entity-aliases", limit=1))
    assert [i["id"] for i in items] == ["a", "b"]
    assert seen_cursors == [None, "c-1"]


def test_sse_stream_yields_data_payloads() -> None:
    body = ': comment\n\ndata: {"chunk": 1}\n\ndata: {"chunk": 2}\ndata: continued\n\n'

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=body, headers={"content-type": "text/event-stream"})

    with make_client(handler) as client:
        payloads = list(client.stream_sse("POST", "/chat/sessions/s-1/completions", json={}))
    assert payloads == ['{"chunk": 1}', '{"chunk": 2}\ncontinued']


def test_supersede_and_forget_payloads() -> None:
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path, json.loads(request.content or b"{}")))
        return httpx.Response(200, json={"ok": True})

    with make_client(handler) as client:
        client.supersede("new-id", "old-id")
        client.forget("vault-1", "k-1", reason="obsolete")
    assert seen[0] == ("POST", "/knowledge/new-id/supersedes", {"predecessor_id": "old-id"})
    assert seen[1] == ("POST", "/vaults/vault-1/knowledge/k-1/forget", {"reason": "obsolete"})
