from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter

import httpx

from backend.app.models.endpoint import Endpoint
from backend.app.models.event import Event


@dataclass
class WebhookSendResult:
    status: str
    response_code: int | None
    latency_ms: int
    failure_type: str | None
    error_message: str | None


def build_webhook_payload(event: Event) -> bytes:
    body = {
        "id": str(event.id),
        "type": event.event_type,
        "payload": event.payload,
        "created_at": event.created_at.isoformat(),
    }
    return json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")


def build_signature(secret: str, timestamp: str, raw_body: bytes) -> str:
    signed_payload = f"{timestamp}.".encode("utf-8") + raw_body
    digest = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def classify_failure(status_code: int | None, exc: Exception | None = None) -> tuple[str, str | None]:
    if exc is not None:
        if isinstance(exc, httpx.TimeoutException):
            return "retrying", "timeout"
        if isinstance(exc, httpx.ConnectError):
            return "retrying", "connection_error"
        return "retrying", "request_error"

    if status_code is None:
        return "retrying", "unknown"
    if 200 <= status_code < 300:
        return "succeeded", None
    if 400 <= status_code < 500:
        return "failed", "client_error"
    if 500 <= status_code < 600:
        return "retrying", "server_error"
    return "retrying", "unexpected_response"


async def send_webhook(endpoint: Endpoint, event: Event, timeout_seconds: float = 10.0) -> WebhookSendResult:
    raw_body = build_webhook_payload(event)
    timestamp = str(int(datetime.now(timezone.utc).timestamp()))
    signature = build_signature(endpoint.signing_secret, timestamp, raw_body)
    headers = {
        "Content-Type": "application/json",
        "X-HookHub-Event-Id": str(event.id),
        "X-HookHub-Timestamp": timestamp,
        "X-HookHub-Signature": signature,
    }

    start = perf_counter()
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.post(endpoint.target_url, content=raw_body, headers=headers)
        latency_ms = int((perf_counter() - start) * 1000)
        status, failure_type = classify_failure(response.status_code)
        return WebhookSendResult(
            status=status,
            response_code=response.status_code,
            latency_ms=latency_ms,
            failure_type=failure_type,
            error_message=None if failure_type is None else f"Webhook returned HTTP {response.status_code}",
        )
    except httpx.HTTPError as exc:
        latency_ms = int((perf_counter() - start) * 1000)
        status, failure_type = classify_failure(None, exc)
        return WebhookSendResult(
            status=status,
            response_code=None,
            latency_ms=latency_ms,
            failure_type=failure_type,
            error_message=str(exc),
        )
