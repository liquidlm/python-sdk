"""Exceptions raised by the LiquidLM Python client.

Exceptions never include request or response bodies: they carry the HTTP
status, the server request identifier and a short safe message only.
"""

from __future__ import annotations

from typing import Any


class LiquidLMError(Exception):
    """Base error for transport, protocol and API failures."""

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.request_id = request_id

    def __repr__(self) -> str:
        parts = [f"status={self.status}", f"request_id={self.request_id}"]
        return f"{type(self).__name__}({self.args[0]!r}, {', '.join(parts)})"


class AuthenticationError(LiquidLMError):
    """HTTP 401/403: credentials are missing, invalid or out of scope."""


class NotFoundError(LiquidLMError):
    """HTTP 404: the addressed resource does not exist or is not visible."""


class RateLimitError(LiquidLMError):
    """HTTP 429: the server asked the client to slow down."""

    def __init__(self, message: str, *, retry_after: float | None = None, **kw: Any) -> None:
        super().__init__(message, **kw)
        self.retry_after = retry_after


class ConflictError(LiquidLMError):
    """HTTP 409: the request conflicts with current server state."""


class ServerError(LiquidLMError):
    """HTTP 5xx: the server failed to answer a well-formed request."""


def error_for_status(status: int, request_id: str | None) -> LiquidLMError:
    """Map a status code to a safe exception without response bodies."""
    message = f"LiquidLM API request failed (HTTP {status})"
    if status in (401, 403):
        return AuthenticationError(message, status=status, request_id=request_id)
    if status == 404:
        return NotFoundError(message, status=status, request_id=request_id)
    if status == 409:
        return ConflictError(message, status=status, request_id=request_id)
    if status == 429:
        return RateLimitError(message, status=status, request_id=request_id)
    if status >= 500:
        return ServerError(message, status=status, request_id=request_id)
    return LiquidLMError(message, status=status, request_id=request_id)
