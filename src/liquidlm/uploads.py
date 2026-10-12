"""File upload orchestration using the contract's attempt-v1 protocol.

Presign returns a storage URL; the bytes go to that URL **without** the API
credentials, then a finalize call commits the attempt. A failed or timed-out
PUT is never replayed implicitly: reconciliation happens through
``/upload/reconcile`` so an ambiguous attempt cannot duplicate content.
"""

from __future__ import annotations

import hashlib
import os
import uuid
from typing import TYPE_CHECKING, Any, BinaryIO, cast

from .errors import LiquidLMError

if TYPE_CHECKING:
    from .client import AsyncLiquidLM, LiquidLM


def _read_all(file: BinaryIO | bytes) -> bytes:
    if isinstance(file, bytes):
        return file
    data = file.read()
    if not isinstance(data, bytes):
        raise TypeError("file-like objects must be opened in binary mode")
    return data


def _validate_upload_url(upload_url: str, api_base_url: str) -> None:
    from urllib.parse import urlparse

    parsed = urlparse(upload_url)
    if parsed.scheme != "https" and parsed.hostname not in ("localhost", "127.0.0.1"):
        raise LiquidLMError(f"Refusing insecure upload URL: {parsed.scheme or 'unknown scheme'}")
    api = urlparse(api_base_url)
    if parsed.hostname == api.hostname and not parsed.path.startswith("/vaults/"):
        raise LiquidLMError("Presigned upload URL points at the API root without a vault path")


def upload_file(
    client: LiquidLM, vault_id: str, file: BinaryIO | bytes, *, file_name: str, content_type: str
) -> dict[str, Any]:
    data = _read_all(file)
    attempt_id = str(uuid.uuid4())
    digest = hashlib.sha256(data).hexdigest()
    presign = client.request(
        "POST",
        f"/vaults/{vault_id}/upload/presign",
        json={
            "fileName": file_name,
            "fileSize": len(data),
            "contentType": content_type,
            "contentSha256Hex": digest,
            "protocol": "attempt-v1",
            "attemptId": attempt_id,
        },
    )
    if presign.get("protocol") != "attempt-v1" or presign.get("attemptId") != attempt_id:
        raise LiquidLMError("Presign response does not match the requested upload attempt")
    upload_url = presign["uploadUrl"]
    _validate_upload_url(upload_url, client.base_url)

    # The storage PUT carries no API credentials on purpose.
    put = client.raw_request("PUT", upload_url, content=data, auth=False)
    if put.status_code >= 400:
        raise LiquidLMError(
            f"Storage upload failed (HTTP {put.status_code})", status=put.status_code
        )
    version_id = put.headers.get("x-amz-version-id")

    return cast(
        "dict[str, Any]",
        client.request(
            "POST",
            f"/vaults/{vault_id}/upload/finalize",
            json={
                "fileName": file_name,
                "fileSize": len(data),
                "hash": digest,
                "s3VersionId": version_id,
                "attemptId": attempt_id,
            },
        ),
    )


async def upload_file_async(
    client: AsyncLiquidLM,
    vault_id: str,
    file: BinaryIO | bytes,
    *,
    file_name: str,
    content_type: str,
) -> dict[str, Any]:
    data = _read_all(file)
    attempt_id = str(uuid.uuid4())
    digest = hashlib.sha256(data).hexdigest()
    presign = await client.request(
        "POST",
        f"/vaults/{vault_id}/upload/presign",
        json={
            "fileName": file_name,
            "fileSize": len(data),
            "contentType": content_type,
            "contentSha256Hex": digest,
            "protocol": "attempt-v1",
            "attemptId": attempt_id,
        },
    )
    if presign.get("protocol") != "attempt-v1" or presign.get("attemptId") != attempt_id:
        raise LiquidLMError("Presign response does not match the requested upload attempt")
    upload_url = presign["uploadUrl"]
    _validate_upload_url(upload_url, client.base_url)

    put = await client.raw_request("PUT", upload_url, content=data, auth=False)
    if put.status_code >= 400:
        raise LiquidLMError(
            f"Storage upload failed (HTTP {put.status_code})", status=put.status_code
        )
    version_id = put.headers.get("x-amz-version-id")

    return cast(
        "dict[str, Any]",
        await client.request(
            "POST",
            f"/vaults/{vault_id}/upload/finalize",
            json={
                "fileName": file_name,
                "fileSize": len(data),
                "hash": digest,
                "s3VersionId": version_id,
                "attemptId": attempt_id,
            },
        ),
    )


def file_content_type(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    return {
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".mp3": "audio/mpeg",
        ".mp4": "video/mp4",
    }.get(ext, "application/octet-stream")
