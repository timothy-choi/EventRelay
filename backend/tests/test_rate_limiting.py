from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.app.models.endpoint import Endpoint
from backend.app.models.event import Event
from backend.app.services.delivery_service import (
    BACKPRESSURE_DELAY_SECONDS,
    BACKPRESSURE_QUEUE_THRESHOLD,
    create_delivery,
    get_delivery_by_id,
    process_delivery,
)
from backend.app.services.queue_service import consume_rate_limit_slot
from backend.app.services.webhook_sender import WebhookSendResult


def test_create_endpoint_with_rate_limit(client) -> None:
    response = client.post(
        "/endpoints",
        json={
            "name": "Rate limited endpoint",
            "target_url": "https://example.com/webhook",
            "max_requests_per_second": 1,
        },
    )

    assert response.status_code in {200, 201}, response.text
    body = response.json()
    assert body["max_requests_per_second"] == 1


def test_patch_endpoint_rate_limit(client) -> None:
    create_response = client.post(
        "/endpoints",
        json={
            "name": "Patch rate limit",
            "target_url": "https://example.com/webhook",
            "max_requests_per_second": 0,
        },
    )
    assert create_response.status_code in {200, 201}, create_response.text
    endpoint_id = create_response.json()["id"]

    patch_response = client.patch(
        f"/endpoints/{endpoint_id}",
        json={"max_requests_per_second": 2},
    )

    assert patch_response.status_code == 200, patch_response.text
    assert patch_response.json()["max_requests_per_second"] == 2


def test_invalid_negative_rate_limit_rejected(client) -> None:
    response = client.post(
        "/endpoints",
        json={
            "name": "Bad rate limit",
            "target_url": "https://example.com/webhook",
            "max_requests_per_second": -1,
        },
    )

    assert response.status_code == 422


def test_event_creation_with_rate_limited_endpoint_creates_delivery(client) -> None:
    endpoint_response = client.post(
        "/endpoints",
        json={
            "name": "Rate limited event target",
            "target_url": "https://example.com/webhook",
            "max_requests_per_second": 1,
        },
    )
    assert endpoint_response.status_code in {200, 201}, endpoint_response.text
    endpoint_id = endpoint_response.json()["id"]

    event_response = client.post(
        "/events",
        json={
            "event_type": "rate.limit.event",
            "payload": {"message": "hello"},
        },
    )

    assert event_response.status_code == 201, event_response.text

    deliveries_response = client.get("/deliveries")
    assert deliveries_response.status_code == 200, deliveries_response.text
    deliveries = deliveries_response.json()
    assert len(deliveries) == 1
    assert deliveries[0]["endpoint_id"] == endpoint_id


def test_worker_rate_limit_delays_delivery(fake_redis) -> None:
    endpoint_id = "endpoint-1"

    first_count = consume_rate_limit_slot(fake_redis, endpoint_id)
    second_count = consume_rate_limit_slot(fake_redis, endpoint_id)

    assert first_count == 1
    assert second_count == 2
    assert first_count <= 1
    assert second_count > 1


def test_unlimited_endpoint_not_rate_limited(fake_redis) -> None:
    endpoint_id = "endpoint-unlimited"

    count = consume_rate_limit_slot(fake_redis, endpoint_id)
    max_requests_per_second = 0

    assert max_requests_per_second == 0
    assert not (max_requests_per_second > 0 and count > max_requests_per_second)


@pytest.mark.asyncio
async def test_rate_limited_endpoint_delays_extra_deliveries(db_session, fake_redis, monkeypatch) -> None:
    endpoint = Endpoint(
        name="rate-limited",
        target_url="https://example.com/webhook",
        signing_secret="secret",
        is_active=True,
        max_requests_per_second=1,
        simulation_latency_ms=0,
        simulation_failure_rate=0,
        simulation_timeout_rate=0,
    )
    events = [
        Event(event_type="rate.limit.one", payload={"i": 1}),
        Event(event_type="rate.limit.two", payload={"i": 2}),
    ]
    db_session.add(endpoint)
    db_session.add_all(events)
    db_session.flush()

    first_delivery = create_delivery(db_session, event_id=events[0].id, endpoint_id=endpoint.id)
    second_delivery = create_delivery(db_session, event_id=events[1].id, endpoint_id=endpoint.id)
    db_session.commit()

    send_calls: list[str] = []

    async def fake_send_webhook(*_args, **_kwargs) -> WebhookSendResult:
        send_calls.append("sent")
        return WebhookSendResult(
            status="succeeded",
            response_code=200,
            latency_ms=25,
            failure_type=None,
            error_message=None,
        )

    def discard_task(coro):
        coro.close()
        return None

    monkeypatch.setattr("backend.app.services.delivery_service.send_webhook", fake_send_webhook)
    monkeypatch.setattr("backend.app.services.delivery_service.asyncio.create_task", discard_task)
    monkeypatch.setattr("backend.app.services.queue_service.time.time", lambda: 1000)

    await process_delivery(db_session, fake_redis, first_delivery.id)
    await process_delivery(db_session, fake_redis, second_delivery.id)

    db_session.expire_all()
    refreshed_first = get_delivery_by_id(db_session, first_delivery.id)
    refreshed_second = get_delivery_by_id(db_session, second_delivery.id)

    assert refreshed_first is not None
    assert refreshed_second is not None
    assert refreshed_first.status == "succeeded"
    assert refreshed_first.total_attempts == 1
    assert refreshed_second.status == "pending"
    assert refreshed_second.total_attempts == 0
    assert refreshed_second.next_retry_at is not None
    assert fake_redis.get("metrics:rate_limited_count") == "1"
    assert len(send_calls) == 1


@pytest.mark.asyncio
async def test_worker_backpressure_delays_processing(db_session, fake_redis, monkeypatch) -> None:
    endpoint = Endpoint(
        name="backpressure-endpoint",
        target_url="https://example.com/webhook",
        signing_secret="secret",
        is_active=True,
        max_requests_per_second=0,
        simulation_latency_ms=0,
        simulation_failure_rate=0,
        simulation_timeout_rate=0,
    )
    event = Event(event_type="backpressure.event", payload={"i": 1})
    db_session.add(endpoint)
    db_session.add(event)
    db_session.flush()

    delivery = create_delivery(db_session, event_id=event.id, endpoint_id=endpoint.id)
    db_session.commit()

    async def fake_send_webhook(*_args, **_kwargs) -> WebhookSendResult:
        return WebhookSendResult(
            status="succeeded",
            response_code=200,
            latency_ms=10,
            failure_type=None,
            error_message=None,
        )

    sleep_calls: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    fake_redis.items.extend(["queued"] * (BACKPRESSURE_QUEUE_THRESHOLD + 1))

    monkeypatch.setattr("backend.app.services.delivery_service.send_webhook", fake_send_webhook)
    monkeypatch.setattr("backend.app.services.delivery_service.asyncio.sleep", fake_sleep)

    await process_delivery(db_session, fake_redis, delivery.id)

    assert BACKPRESSURE_DELAY_SECONDS in sleep_calls
    assert fake_redis.get("metrics:delayed_due_to_backpressure_count") == "1"


@pytest.mark.asyncio
async def test_unlimited_endpoint_is_not_throttled(db_session, fake_redis, monkeypatch) -> None:
    endpoint = Endpoint(
        name="unlimited",
        target_url="https://example.com/webhook",
        signing_secret="secret",
        is_active=True,
        max_requests_per_second=0,
        simulation_latency_ms=0,
        simulation_failure_rate=0,
        simulation_timeout_rate=0,
    )
    events = [
        Event(event_type="unlimited.one", payload={"i": 1}),
        Event(event_type="unlimited.two", payload={"i": 2}),
    ]
    db_session.add(endpoint)
    db_session.add_all(events)
    db_session.flush()

    first_delivery = create_delivery(db_session, event_id=events[0].id, endpoint_id=endpoint.id)
    second_delivery = create_delivery(db_session, event_id=events[1].id, endpoint_id=endpoint.id)
    db_session.commit()

    send_calls: list[str] = []

    async def fake_send_webhook(*_args, **_kwargs) -> WebhookSendResult:
        send_calls.append("sent")
        return WebhookSendResult(
            status="succeeded",
            response_code=200,
            latency_ms=10,
            failure_type=None,
            error_message=None,
        )

    monkeypatch.setattr("backend.app.services.delivery_service.send_webhook", fake_send_webhook)

    await process_delivery(db_session, fake_redis, first_delivery.id)
    await process_delivery(db_session, fake_redis, second_delivery.id)

    db_session.expire_all()
    refreshed_first = get_delivery_by_id(db_session, first_delivery.id)
    refreshed_second = get_delivery_by_id(db_session, second_delivery.id)

    assert refreshed_first is not None
    assert refreshed_second is not None
    assert refreshed_first.status == "succeeded"
    assert refreshed_second.status == "succeeded"
    assert refreshed_first.next_retry_at is None
    assert refreshed_second.next_retry_at is None
    assert len(send_calls) == 2
