"""Async variant of the synthetic ingest/search/get/forget journey."""

from __future__ import annotations

import asyncio

from liquidlm import AsyncLiquidLM
from sync_ingest_search import NOTE, VAULT, fixture_transport


async def main() -> None:
    async with AsyncLiquidLM(
        "https://api.example.test", token="synthetic", transport=fixture_transport()
    ) as client:
        created = await client.put_knowledge(type="note", title="runbook", body="synthetic body")
        found = await client.search_hybrid("runbook", limit=1)
        fetched = await client.get_knowledge(created["id"])
        forgotten = await client.forget(VAULT, fetched["id"], reason="example cleanup")
        assert found["results"][0]["id"] == NOTE
        print("async ingest -> search -> get -> forget completed:", forgotten["ok"])


if __name__ == "__main__":
    asyncio.run(main())
