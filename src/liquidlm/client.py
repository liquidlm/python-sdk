"""Sync and async clients for the LiquidLM public API.

One transport abstraction (httpx) backs both clients. Arbitrary HTTP methods
are allowed so ``/search/hybrid`` uses ``QUERY`` without a transport hack.
Mutation requests are never retried automatically; bounded read retries cover
429/5xx responses with jittered backoff and Retry-After support.
"""

from __future__ import annotations

import asyncio
import random
import time
from collections.abc import AsyncIterator, Iterator
from typing import Any, cast

import httpx

from ._pagination import (
    paginate_cursor,
    paginate_cursor_async,
    paginate_offset,
    paginate_offset_async,
)
from ._sse import parse_sse, parse_sse_async
from .errors import error_for_status

DEFAULT_BASE_URL = "https://api.liquidlm.com"
READ_METHODS = frozenset({"GET", "HEAD", "QUERY", "OPTIONS"})


class _BaseClient:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        token: str | None = None,
        active_org: str | None = None,
        *,
        timeout: float = 30.0,
        max_read_retries: int = 2,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._token = token
        self._active_org = active_org
        self._timeout = timeout
        self._max_read_retries = max_read_retries

    def _headers(self, extra: dict[str, str] | None, *, json_body: bool) -> dict[str, str]:
        headers: dict[str, str] = {"Accept": "application/json"}
        if json_body:
            headers["Content-Type"] = "application/json"
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        if self._active_org:
            headers["X-LiquidLM-Active-Org"] = self._active_org
        headers.update(extra or {})
        return headers

    @staticmethod
    def _backoff(attempt: int, retry_after: str | None) -> float:
        if retry_after:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                pass
        return min(2.0**attempt, 8.0) + random.random() * 0.1

    @staticmethod
    def _should_retry(method: str, status: int) -> bool:
        return method in READ_METHODS and status in (429, 500, 502, 503, 504)

    @staticmethod
    def _decode(response: httpx.Response) -> Any:
        if response.status_code == 204 or not response.content:
            return None
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        return response.content

    def _check(self, response: httpx.Response) -> None:
        if response.status_code >= 400:
            raise error_for_status(response.status_code, response.headers.get("x-request-id"))

    # Typed convenience helpers live on both clients; everything else is
    # reachable through request() with the same auth/error semantics.


class LiquidLM(_BaseClient):
    """Synchronous client. Use as a context manager to close connections."""

    def __init__(
        self, *args: Any, transport: httpx.BaseTransport | None = None, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self._client = httpx.Client(timeout=self._timeout, transport=transport)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> LiquidLM:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def raw_request(
        self,
        method: str,
        url: str,
        *,
        content: bytes | None = None,
        auth: bool = True,
    ) -> httpx.Response:
        headers = self._headers(None, json_body=False) if auth else {}
        return self._client.request(method, url, content=content, headers=headers)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        method = method.upper()
        attempt = 0
        while True:
            response = self._client.request(
                method,
                url,
                params=params,
                json=json,
                headers=self._headers(headers, json_body=json is not None),
            )
            if response.status_code < 400:
                return self._decode(response)
            retry_after = response.headers.get("retry-after")
            if attempt < self._max_read_retries and self._should_retry(
                method, response.status_code
            ):
                time.sleep(self._backoff(attempt, retry_after))
                attempt += 1
                continue
            self._check(response)

    def stream_sse(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
    ) -> Iterator[str]:
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        with self._client.stream(
            method.upper(),
            url,
            json=json,
            headers=self._headers({"Accept": "text/event-stream"}, json_body=json is not None),
        ) as response:
            self._check(response)
            yield from parse_sse(response.iter_lines())

    # -- typed helpers for the harness-critical workflows -------------------
    def search_hybrid(self, query: str, **options: Any) -> dict[str, Any]:
        return cast(
            "dict[str, Any]",
            self.request("QUERY", "/search/hybrid", json={"query": query, **options}),
        )

    def search_fulltext(self, query: str, **options: Any) -> dict[str, Any]:
        return cast(
            "dict[str, Any]",
            self.request("QUERY", "/search/fulltext", json={"query": query, **options}),
        )

    def get_knowledge(self, knowledge_id: str) -> dict[str, Any]:
        return cast("dict[str, Any]", self.request("GET", f"/knowledge/{knowledge_id}"))

    def list_knowledge(self, *, limit: int = 100, **params: Any) -> Iterator[dict[str, Any]]:
        return paginate_offset(self, "/knowledge", params=params, limit=limit)

    def list_offset(
        self, path: str, *, limit: int = 100, **params: Any
    ) -> Iterator[dict[str, Any]]:
        return paginate_offset(self, path, params=params, limit=limit)

    def list_cursor(
        self, path: str, *, limit: int = 100, **params: Any
    ) -> Iterator[dict[str, Any]]:
        return paginate_cursor(self, path, params=params, limit=limit)

    def put_knowledge(
        self, *, type: str, title: str, body: str | None = None, **fields: Any
    ) -> Any:
        payload = {"type": type, "title": title, **fields}
        if body is not None:
            payload["body"] = body
        return self.request("POST", "/knowledge", json=payload)

    def patch_knowledge(self, knowledge_id: str, **fields: Any) -> dict[str, Any]:
        return cast(
            "dict[str, Any]", self.request("PATCH", f"/knowledge/{knowledge_id}", json=fields)
        )

    def supersede(self, knowledge_id: str, predecessor_id: str) -> Any:
        return self.request(
            "POST", f"/knowledge/{knowledge_id}/supersedes", json={"predecessor_id": predecessor_id}
        )

    def forget(
        self, vault_id: str, knowledge_id: str, *, reason: str | None = None
    ) -> dict[str, Any]:
        payload = {"reason": reason} if reason else {}
        return cast(
            "dict[str, Any]",
            self.request(
                "POST", f"/vaults/{vault_id}/knowledge/{knowledge_id}/forget", json=payload
            ),
        )

    def upload_file(
        self, vault_id: str, file: Any, *, file_name: str, content_type: str
    ) -> dict[str, Any]:
        from .uploads import upload_file

        return upload_file(self, vault_id, file, file_name=file_name, content_type=content_type)


class AsyncLiquidLM(_BaseClient):
    """Asynchronous client with the same contract as ``LiquidLM``."""

    def __init__(
        self, *args: Any, transport: httpx.AsyncBaseTransport | None = None, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self._client = httpx.AsyncClient(timeout=self._timeout, transport=transport)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> AsyncLiquidLM:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    async def raw_request(
        self,
        method: str,
        url: str,
        *,
        content: bytes | None = None,
        auth: bool = True,
    ) -> httpx.Response:
        headers = self._headers(None, json_body=False) if auth else {}
        return await self._client.request(method, url, content=content, headers=headers)

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        method = method.upper()
        attempt = 0
        while True:
            response = await self._client.request(
                method,
                url,
                params=params,
                json=json,
                headers=self._headers(headers, json_body=json is not None),
            )
            if response.status_code < 400:
                return self._decode(response)
            retry_after = response.headers.get("retry-after")
            if attempt < self._max_read_retries and self._should_retry(
                method, response.status_code
            ):
                await asyncio.sleep(self._backoff(attempt, retry_after))
                attempt += 1
                continue
            self._check(response)

    async def stream_sse(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
    ) -> AsyncIterator[str]:
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        async with self._client.stream(
            method.upper(),
            url,
            json=json,
            headers=self._headers({"Accept": "text/event-stream"}, json_body=json is not None),
        ) as response:
            self._check(response)
            async for payload in parse_sse_async(response.aiter_lines()):
                yield payload

    # -- typed helpers -------------------------------------------------------
    async def search_hybrid(self, query: str, **options: Any) -> dict[str, Any]:
        return cast(
            "dict[str, Any]",
            await self.request("QUERY", "/search/hybrid", json={"query": query, **options}),
        )

    async def search_fulltext(self, query: str, **options: Any) -> dict[str, Any]:
        return cast(
            "dict[str, Any]",
            await self.request("QUERY", "/search/fulltext", json={"query": query, **options}),
        )

    async def get_knowledge(self, knowledge_id: str) -> dict[str, Any]:
        return cast("dict[str, Any]", await self.request("GET", f"/knowledge/{knowledge_id}"))

    def list_knowledge(self, *, limit: int = 100, **params: Any) -> AsyncIterator[dict[str, Any]]:
        return paginate_offset_async(self, "/knowledge", params=params, limit=limit)

    def list_offset(
        self, path: str, *, limit: int = 100, **params: Any
    ) -> AsyncIterator[dict[str, Any]]:
        return paginate_offset_async(self, path, params=params, limit=limit)

    def list_cursor(
        self, path: str, *, limit: int = 100, **params: Any
    ) -> AsyncIterator[dict[str, Any]]:
        return paginate_cursor_async(self, path, params=params, limit=limit)

    async def put_knowledge(
        self, *, type: str, title: str, body: str | None = None, **fields: Any
    ) -> Any:
        payload = {"type": type, "title": title, **fields}
        if body is not None:
            payload["body"] = body
        return await self.request("POST", "/knowledge", json=payload)

    async def patch_knowledge(self, knowledge_id: str, **fields: Any) -> dict[str, Any]:
        return cast(
            "dict[str, Any]", await self.request("PATCH", f"/knowledge/{knowledge_id}", json=fields)
        )

    async def supersede(self, knowledge_id: str, predecessor_id: str) -> Any:
        return await self.request(
            "POST", f"/knowledge/{knowledge_id}/supersedes", json={"predecessor_id": predecessor_id}
        )

    async def forget(
        self, vault_id: str, knowledge_id: str, *, reason: str | None = None
    ) -> dict[str, Any]:
        payload = {"reason": reason} if reason else {}
        return cast(
            "dict[str, Any]",
            await self.request(
                "POST", f"/vaults/{vault_id}/knowledge/{knowledge_id}/forget", json=payload
            ),
        )

    async def upload_file(
        self, vault_id: str, file: Any, *, file_name: str, content_type: str
    ) -> dict[str, Any]:
        from .uploads import upload_file_async

        return await upload_file_async(
            self, vault_id, file, file_name=file_name, content_type=content_type
        )
