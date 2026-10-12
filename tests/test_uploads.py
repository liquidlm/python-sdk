"""Upload attempt protocol: presign, credential-free storage PUT, finalize."""

from __future__ import annotations

import hashlib
import json

import httpx
import pytest

from liquidlm import LiquidLM
from liquidlm.errors import LiquidLMError

DATA = b"synthetic upload bytes"
DIGEST = hashlib.sha256(DATA).hexdigest()
ATTEMPT = "attempt-v1"


def make_flow_client(record: dict) -> LiquidLM:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/upload/presign"):
            record["presign"] = json.loads(request.content)
            return httpx.Response(
                200,
                json={
                    "protocol": ATTEMPT,
                    "attemptId": record["presign"]["attemptId"],
                    "uploadUrl": "https://storage.example.test/bucket/key?signature=abc",
                    "s3Key": "key",
                    "expiresAt": "2026-10-11T00:00:00Z",
                },
            )
        if request.url.host == "storage.example.test":
            record["put_auth"] = request.headers.get("authorization")
            record["put_body"] = request.content
            return httpx.Response(200, headers={"x-amz-version-id": "v-9"})
        if request.url.path.endswith("/upload/finalize"):
            record["finalize"] = json.loads(request.content)
            return httpx.Response(
                200, json={"ok": True, "knowledgeId": "k-1", "state": "committed"}
            )
        raise AssertionError(f"unexpected request: {request.url}")

    return LiquidLM(
        "https://api.example.test", token="synthetic-token", transport=httpx.MockTransport(handler)
    )


def test_upload_flow_sends_no_credentials_to_storage() -> None:
    record: dict = {}
    with make_flow_client(record) as client:
        result = client.upload_file(
            "vault-1", DATA, file_name="notes.txt", content_type="text/plain"
        )
    assert result["knowledgeId"] == "k-1"
    assert record["presign"]["contentSha256Hex"] == DIGEST
    assert record["presign"]["protocol"] == ATTEMPT
    assert record["put_auth"] is None, "storage PUT must not carry API credentials"
    assert record["put_body"] == DATA
    assert record["finalize"]["hash"] == DIGEST
    assert record["finalize"]["s3VersionId"] == "v-9"
    assert record["finalize"]["attemptId"] == record["presign"]["attemptId"]


def test_presign_protocol_mismatch_is_rejected() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"protocol": "legacy", "attemptId": "other"})

    client = LiquidLM("https://api.example.test", token="t", transport=httpx.MockTransport(handler))
    with pytest.raises(LiquidLMError, match="does not match"):
        client.upload_file(
            "vault-1", DATA, file_name="f.bin", content_type="application/octet-stream"
        )


def test_insecure_upload_url_is_refused() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "protocol": ATTEMPT,
                "attemptId": body["attemptId"],
                "uploadUrl": "http://storage.example.test/key",
                "s3Key": "key",
                "expiresAt": "2026-10-11T00:00:00Z",
            },
        )

    client = LiquidLM("https://api.example.test", token="t", transport=httpx.MockTransport(handler))
    with pytest.raises(LiquidLMError, match="insecure"):
        client.upload_file(
            "vault-1", DATA, file_name="f.bin", content_type="application/octet-stream"
        )


def test_failed_storage_put_is_not_replayed() -> None:
    calls = {"put": 0, "finalize": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/upload/presign"):
            body = json.loads(request.content)
            return httpx.Response(
                200,
                json={
                    "protocol": ATTEMPT,
                    "attemptId": body["attemptId"],
                    "uploadUrl": "https://storage.example.test/key",
                    "s3Key": "key",
                    "expiresAt": "2026-10-11T00:00:00Z",
                },
            )
        if request.url.host == "storage.example.test":
            calls["put"] += 1
            return httpx.Response(503)
        calls["finalize"] += 1
        return httpx.Response(200, json={})

    client = LiquidLM("https://api.example.test", token="t", transport=httpx.MockTransport(handler))
    with pytest.raises(LiquidLMError, match="Storage upload failed"):
        client.upload_file(
            "vault-1", DATA, file_name="f.bin", content_type="application/octet-stream"
        )
    assert calls == {"put": 1, "finalize": 0}
