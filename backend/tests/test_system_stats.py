from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from backend.app.models.delivery import Delivery
from backend.app.models.delivery_attempt import DeliveryAttempt
from backend.app.models.event import Event


def test_system_stats_returns_aggregated_metrics(client, db_session, fake_redis) -> None:
    endpoint_response = client.post(
        "/endpoints",
        json={
            "name": "System stats endpoint",
            "target_url": "https://example.com/webhook",
        },
    )
    assert endpoint_response.status_code == 201
    endpoint_id = UUID(endpoint_response.json()["id"])

    now = datetime.now(timezone.utc)
    events = [
        Event(event_type="system.one", payload={"i": 1}),
        Event(event_type="system.two", payload={"i": 2}),
    ]
    db_session.add_all(events)
    db_session.flush()

    deliveries = [
        Delivery(
            event_id=events[0].id,
            endpoint_id=endpoint_id,
            status="succeeded",
            total_attempts=1,
            created_at=now,
            updated_at=now,
        ),
        Delivery(
            event_id=events[1].id,
            endpoint_id=endpoint_id,
            status="failed",
            total_attempts=2,
            last_error="http_5xx: 503",
            created_at=now,
            updated_at=now,
        ),
    ]
    db_session.add_all(deliveries)
    db_session.flush()

    attempts = [
        DeliveryAttempt(
            delivery_id=deliveries[0].id,
            attempt_number=1,
            status="succeeded",
            response_code=200,
            latency_ms=100,
            started_at=now,
            completed_at=now,
        ),
        DeliveryAttempt(
            delivery_id=deliveries[1].id,
            attempt_number=1,
            status="retrying",
            response_code=503,
            latency_ms=200,
            failure_type="http_5xx",
            error_message="http_5xx: 503",
            started_at=now,
            completed_at=now,
        ),
        DeliveryAttempt(
            delivery_id=deliveries[1].id,
            attempt_number=2,
            status="failed",
            response_code=503,
            latency_ms=300,
            failure_type="http_5xx",
            error_message="http_5xx: 503",
            started_at=now,
            completed_at=now,
        ),
    ]
    db_session.add_all(attempts)
    db_session.commit()

    fake_redis.set("metrics:rate_limited_count", 2)
    fake_redis.set("metrics:delayed_due_to_backpressure_count", 3)
    fake_redis.items.extend(["queued-a", "queued-b"])

    response = client.get("/system/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["total_events_processed"] == 2
    assert body["total_deliveries"] == 2
    assert body["total_attempts"] == 3
    assert body["success_rate"] == 50.0
    assert body["avg_latency_ms"] == 200.0
    assert body["p95_latency_ms"] == 300.0
    assert body["rate_limited_count"] == 2
    assert body["delayed_due_to_backpressure_count"] == 3
    assert body["current_queue_depth"] == 2
