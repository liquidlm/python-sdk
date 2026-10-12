"""Synthetic end-to-end example: ingest a note, search it, read it, forget it.

Runs against a local fixture transport — no account, credentials or network
are involved. Swap ``fixture_transport()`` for the default transport and set
``LIQUIDLM_API_TOKEN`` to run against a real deployment.
"""

from __future__ import annotations

import json

import httpx

from liquidlm import LiquidLM

VAULT = "11111111-1111-4111-8111-111111111111"
NOTE = "22222222-2222-4222-8222-222222222222"


def fixture_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content or b"{}")
        if request.method == "POST" and request.url.path == "/knowledge":
            return httpx.Response(201, json={"id": NOTE, "vault_id": VAULT, **body})
        if request.method == "QUERY" and request.url.path == "/search/hybrid":
            return httpx.Response(200, json={"results": [{"id": NOTE, "title": body["query"]}]})
        if request.method == "GET" and request.url.path == f"/knowledge/{NOTE}":
            return httpx.Response(200, json={"id": NOTE, "type": "note", "title": "runbook"})
        if request.url.path.endswith("/forget"):
            return httpx.Response(
                200,
                json={
                    "ok": True,
                    "forgotten_at": "2026-10-11T00:00:00Z",
                    "forgotten_batch_id": "b-1",
                    "restorable_until": "2026-11-10T00:00:00Z",
                },
            )
        return httpx.Response(404, json={})

    return httpx.MockTransport(handler)


def main() -> None:
    with LiquidLM(
        "https://api.example.test", token="synthetic", transport=fixture_transport()
    ) as client:
        created = client.put_knowledge(type="note", title="runbook", body="synthetic body")
        found = client.search_hybrid("runbook", limit=1)
        fetched = client.get_knowledge(created["id"])
        forgotten = client.forget(VAULT, fetched["id"], reason="example cleanup")
        assert found["results"][0]["id"] == created["id"]
        print("ingest -> search -> get -> forget completed:", forgotten["ok"])


if __name__ == "__main__":
    main()
