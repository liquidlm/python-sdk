"""Pagination helpers shared by the sync and async clients.

Two shapes exist in the public contract: offset/limit lists answering
`{"items": [...], "hasMore": bool}` and cursor lists answering
`{"items": [...], "next_cursor": str | null}`. Callers never hand-construct
either; the helpers drive the client's request method.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .client import AsyncLiquidLM, LiquidLM


def paginate_offset(
    client: LiquidLM,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    limit: int = 100,
) -> Iterator[dict[str, Any]]:
    offset = 0
    while True:
        page = client.request(
            "GET", path, params={**(params or {}), "limit": limit, "offset": offset}
        )
        items = page.get("items", [])
        yield from items
        if not page.get("hasMore") or not items:
            return
        offset += len(items)


def paginate_cursor(
    client: LiquidLM,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    limit: int = 100,
) -> Iterator[dict[str, Any]]:
    cursor: str | None = None
    while True:
        query = {**(params or {}), "limit": limit}
        if cursor:
            query["cursor"] = cursor
        page = client.request("GET", path, params=query)
        items = page.get("items", [])
        yield from items
        cursor = page.get("next_cursor")
        if not cursor or not items:
            return


async def paginate_offset_async(
    client: AsyncLiquidLM,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    limit: int = 100,
) -> AsyncIterator[dict[str, Any]]:
    offset = 0
    while True:
        page = await client.request(
            "GET", path, params={**(params or {}), "limit": limit, "offset": offset}
        )
        items = page.get("items", [])
        for item in items:
            yield item
        if not page.get("hasMore") or not items:
            return
        offset += len(items)


async def paginate_cursor_async(
    client: AsyncLiquidLM,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    limit: int = 100,
) -> AsyncIterator[dict[str, Any]]:
    cursor: str | None = None
    while True:
        query = {**(params or {}), "limit": limit}
        if cursor:
            query["cursor"] = cursor
        page = await client.request("GET", path, params=query)
        items = page.get("items", [])
        for item in items:
            yield item
        cursor = page.get("next_cursor")
        if not cursor or not items:
            return
