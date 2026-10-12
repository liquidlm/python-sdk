"""Minimal server-sent events parser for streaming endpoints.

Yields decoded ``data:`` payloads as strings. Comments, event names and IDs
are not surfaced; the LiquidLM endpoints stream JSON payloads only.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterable, Iterator


def parse_sse(lines: Iterable[str]) -> Iterator[str]:
    buffer: list[str] = []
    for raw in lines:
        line = raw.rstrip("\r\n")
        if not line:
            if buffer:
                yield "\n".join(buffer)
                buffer = []
            continue
        if line.startswith(":"):
            continue
        if line.startswith("data:"):
            buffer.append(line[5:].lstrip(" "))
    if buffer:
        yield "\n".join(buffer)


async def parse_sse_async(lines: AsyncIterator[str]) -> AsyncIterator[str]:
    buffer: list[str] = []
    async for raw in lines:
        line = raw.rstrip("\r\n")
        if not line:
            if buffer:
                yield "\n".join(buffer)
                buffer = []
            continue
        if line.startswith(":"):
            continue
        if line.startswith("data:"):
            buffer.append(line[5:].lstrip(" "))
    if buffer:
        yield "\n".join(buffer)
