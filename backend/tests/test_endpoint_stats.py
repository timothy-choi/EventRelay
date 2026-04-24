from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from backend.app.models.delivery import Delivery
from backend.app.models.delivery_attempt import DeliveryAttempt
from backend.app.models.event import Event


def test_endpoint_stats_missing_endpoint_returns_404(client: TestClient) -> None:
    response = client.get(f"/endpoints/{uuid4()}/stats")

    assert response.status_code == 404
    assert response.json() == {"detail": "Endpoint not found"}


def test_endpoint_stats_with_no_deliveries_returns_zeros(client: TestClient) -> None:
    create_response = client.post(
        "/endpoints",
        json={
            "name": "Stats endpoint",
            "target_url": "https://example.com/webhook",
        },
    )
    assert create_response.status_code in {200, 201}, create_response.text
    endpoint = create_response.json()
    endpoint_id = UUID(endpoint["id"])

    response = client.get(f"/endpoints/{endpoint['id']}/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["endpoint_id"] == endpoint["id"]
    assert body["endpoint_name"] == "Stats endpoint"
    assert body["total_deliveries"] == 0
    assert body["succeeded"] == 0
    assert body["failed"] == 0
    assert body["retrying"] == 0
    assert body["pending"] == 0
    assert body["success_rate"] == 0.0
    assert body["avg_latency_ms"] is None
    assert body["p95_latency_ms"] is None
    assert body["total_attempts"] == 0
    assert body["timeout_count"] == 0
    assert body["connection_error_count"] == 0
    assert body["http_4xx_count"] == 0
    assert body["http_5xx_count"] == 0


def test_endpoint_stats_returns_status_counts_and_latency_metrics(client: TestClient, db_session) -> None:
    create_response = client.post(
        "/endpoints",
        json={
            "name": "Measured endpoint",
            "target_url": "https://example.com/webhook",
        },
    )
    assert create_response.status_code in {200, 201}, create_response.text
    endpoint = create_response.json()
    endpoint_id = UUID(endpoint["id"])

    now = datetime.now(timezone.utc)
    event_one = Event(event_type="stats.one", payload={"i": 1})
    event_two = Event(event_type="stats.two", payload={"i": 2})
    event_three = Event(event_type="stats.three", payload={"i": 3})
    db_session.add_all([event_one, event_two, event_three])
    db_session.flush()

    deliveries = [
        Delivery(
            event_id=event_one.id,
            endpoint_id=endpoint_id,
            status="succeeded",
            total_attempts=2,
            created_at=now,
            updated_at=now,
        ),
        Delivery(
            event_id=event_two.id,
            endpoint_id=endpoint_id,
            status="failed",
            total_attempts=1,
            last_error="http_5xx: 503",
            created_at=now,
            updated_at=now,
        ),
        Delivery(
            event_id=event_three.id,
            endpoint_id=endpoint_id,
            status="retrying",
            total_attempts=1,
            last_error="timeout: request timed out",
            created_at=now,
            updated_at=now,
        ),
        Delivery(
            event_id=event_three.id,
            endpoint_id=endpoint_id,
            status="pending",
            total_attempts=0,
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
            delivery_id=deliveries[0].id,
            attempt_number=2,
            status="succeeded",
            response_code=200,
            latency_ms=200,
            started_at=now,
            completed_at=now,
        ),
        DeliveryAttempt(
            delivery_id=deliveries[1].id,
            attempt_number=1,
            status="failed",
            response_code=500,
            latency_ms=300,
            failure_type="http_5xx",
            error_message="http_5xx: 500",
            started_at=now,
            completed_at=now,
        ),
        DeliveryAttempt(
            delivery_id=deliveries[2].id,
            attempt_number=1,
            status="retrying",
            latency_ms=400,
            failure_type="timeout",
            error_message="timeout: request timed out",
            started_at=now,
            completed_at=now,
        ),
        DeliveryAttempt(
            delivery_id=deliveries[2].id,
            attempt_number=2,
            status="retrying",
            latency_ms=500,
            failure_type="connection_error",
            error_message="connection_error: connection failed",
            started_at=now,
            completed_at=now,
        ),
        DeliveryAttempt(
            delivery_id=deliveries[1].id,
            attempt_number=2,
            status="failed",
            response_code=422,
            latency_ms=600,
            failure_type="http_4xx",
            error_message="http_4xx: 422",
            started_at=now,
            completed_at=now,
        ),
    ]
    db_session.add_all(attempts)
    db_session.commit()

    response = client.get(f"/endpoints/{endpoint['id']}/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["endpoint_id"] == endpoint["id"]
    assert body["endpoint_name"] == "Measured endpoint"
    assert body["total_deliveries"] == 4
    assert body["succeeded"] == 1
    assert body["failed"] == 1
    assert body["retrying"] == 1
    assert body["pending"] == 1
    assert body["success_rate"] == 25.0
    assert body["avg_latency_ms"] == 350.0
    assert body["p95_latency_ms"] == 600
    assert body["total_attempts"] == 6
    assert body["timeout_count"] == 1
    assert body["connection_error_count"] == 1
    assert body["http_4xx_count"] == 1
    assert body["http_5xx_count"] == 1
