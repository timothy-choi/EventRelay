from __future__ import annotations

import hashlib
import hmac
import json
import os
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter

import httpx

from backend.app.models.endpoint import Endpoint
from backend.app.models.event import Event

USE_NETWORK_PROXY = os.getenv("USE_NETWORK_PROXY", "false").lower() == "true"
NETWORK_PROXY_URL = os.getenv("NETWORK_PROXY_URL", "http://proxy:8080/proxy")
DEFAULT_PROXY_LATENCY_MS = os.getenv("NETWORK_PROXY_LATENCY_MS", "300")
DEFAULT_PROXY_TIMEOUT_RATE = os.getenv("NETWORK_PROXY_TIMEOUT_RATE", "0")
DEFAULT_PROXY_FAILURE_RATE = os.getenv("NETWORK_PROXY_FAILURE_RATE", "0")


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


def iter_exception_chain(exc: BaseException) -> list[BaseException]:
    chain: list[BaseException] = []
    current: BaseException | None = exc
    seen: set[int] = set()

    while current is not None and id(current) not in seen:
        seen.add(id(current))
        chain.append(current)
        current = current.__cause__ or current.__context__

    return chain


def classify_error(
    *,
    response: httpx.Response | None = None,
    exc: Exception | None = None,
) -> str | None:
    if exc is not None:
        if isinstance(exc, httpx.TimeoutException):
            return "timeout"
        if isinstance(exc, httpx.ConnectError):
            if _is_dns_error(exc):
                return "dns_error"
            return "connection_error"
        if isinstance(exc, httpx.RequestError):
            if _is_dns_error(exc):
                return "dns_error"
            return "connection_error"
        return "unknown_error"

    if response is None:
        return None
    if 400 <= response.status_code < 500:
        return "http_4xx"
    if 500 <= response.status_code < 600:
        return "http_5xx"
    return None


def is_retryable_failure(failure_type: str | None) -> bool:
    return failure_type in {"timeout", "connection_error", "dns_error", "http_5xx"}


def _is_dns_error(exc: Exception) -> bool:
    dns_markers = (
        "name or service not known",
        "nodename nor servname provided",
        "temporary failure in name resolution",
        "getaddrinfo failed",
        "no address associated with hostname",
        "failed to resolve",
    )
    for current in iter_exception_chain(exc):
        if isinstance(current, socket.gaierror):
            return True
        message = " ".join(str(arg) for arg in current.args if arg).lower()
        if any(marker in message for marker in dns_markers):
            return True
    return False


def build_error_message(
    *,
    response: httpx.Response | None = None,
    exc: Exception | None = None,
    failure_type: str | None = None,
) -> str | None:
    if failure_type is None:
        return None

    if exc is not None:
        if failure_type == "connection_error":
            return "connection_error: connection failed"
        if failure_type == "timeout":
            return "timeout: request timed out"
        if failure_type == "dns_error":
            return "dns_error: DNS lookup failed"
        if failure_type == "unknown_error":
            return "unknown_error: request failed"
        return f"{failure_type}: request failed"

    if response is not None:
        if failure_type in {"http_4xx", "http_5xx"}:
            return f"{failure_type}: {response.status_code}"
        return f"{failure_type}: {response.status_code}"

    return f"{failure_type}: unexpected error"


def resolve_delivery_status(failure_type: str | None) -> str:
    if failure_type is None:
        return "succeeded"
    if is_retryable_failure(failure_type):
        return "retrying"
    return "failed"


def get_delivery_target_url(endpoint: Endpoint) -> str:
    if not USE_NETWORK_PROXY:
        return endpoint.target_url
    return NETWORK_PROXY_URL


def build_delivery_headers(endpoint: Endpoint, event: Event, raw_body: bytes) -> dict[str, str]:
    timestamp = str(int(datetime.now(timezone.utc).timestamp()))
    signature = build_signature(endpoint.signing_secret, timestamp, raw_body)
    headers = {
        "Content-Type": "application/json",
        "X-HookHub-Event-Id": str(event.id),
        "X-HookHub-Timestamp": timestamp,
        "X-HookHub-Signature": signature,
    }
    if USE_NETWORK_PROXY:
        headers.update(
            {
                "X-EventRelay-Target-Url": endpoint.target_url,
                "X-EventRelay-Latency-Ms": DEFAULT_PROXY_LATENCY_MS,
                "X-EventRelay-Timeout-Rate": DEFAULT_PROXY_TIMEOUT_RATE,
                "X-EventRelay-Failure-Rate": DEFAULT_PROXY_FAILURE_RATE,
            }
        )
    return headers


async def send_webhook(endpoint: Endpoint, event: Event, timeout_seconds: float = 10.0) -> WebhookSendResult:
    raw_body = build_webhook_payload(event)
    headers = build_delivery_headers(endpoint, event, raw_body)
    target_url = get_delivery_target_url(endpoint)

    start = perf_counter()
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.post(target_url, content=raw_body, headers=headers)
        latency_ms = int((perf_counter() - start) * 1000)
        failure_type = classify_error(response=response)
        return WebhookSendResult(
            status=resolve_delivery_status(failure_type),
            response_code=response.status_code,
            latency_ms=latency_ms,
            failure_type=failure_type,
            error_message=build_error_message(response=response, failure_type=failure_type),
        )
    except httpx.HTTPError as exc:
        latency_ms = int((perf_counter() - start) * 1000)
        failure_type = classify_error(exc=exc)
        return WebhookSendResult(
            status=resolve_delivery_status(failure_type),
            response_code=None,
            latency_ms=latency_ms,
            failure_type=failure_type,
            error_message=build_error_message(exc=exc, failure_type=failure_type),
        )
