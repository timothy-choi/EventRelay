from __future__ import annotations

from fastapi.testclient import TestClient


def test_event_creation_only_creates_deliveries_for_active_endpoints(client: TestClient) -> None:
    active_response = client.post(
        "/endpoints",
        json={
            "name": "Active endpoint",
            "target_url": "https://example.com/active",
        },
    )
    assert active_response.status_code in {200, 201}, active_response.text
    inactive_response = client.post(
        "/endpoints",
        json={
            "name": "Inactive endpoint",
            "target_url": "https://example.com/inactive",
        },
    )
    assert inactive_response.status_code in {200, 201}, inactive_response.text
    inactive_endpoint_id = inactive_response.json()["id"]

    deactivate_response = client.patch(
        f"/endpoints/{inactive_endpoint_id}",
        json={"is_active": False},
    )
    assert deactivate_response.status_code == 200

    event_response = client.post(
        "/events",
        json={
            "event_type": "test.event",
            "payload": {"message": "hello"},
        },
    )

    assert event_response.status_code == 201

    deliveries_response = client.get("/deliveries")

    assert deliveries_response.status_code == 200
    deliveries = deliveries_response.json()
    assert len(deliveries) == 1
    assert deliveries[0]["endpoint_id"] == active_response.json()["id"]
    assert deliveries[0]["endpoint_name"] == "Active endpoint"


def test_event_creation_with_simulation_config_creates_delivery(client: TestClient) -> None:
    endpoint_response = client.post(
        "/endpoints",
        json={
            "name": "failure-test",
            "target_url": "http://host.docker.internal:9000/webhook",
            "simulation_latency_ms": 100,
            "simulation_failure_rate": 50,
            "simulation_timeout_rate": 0,
        },
    )
    assert endpoint_response.status_code in {200, 201}, endpoint_response.text
    endpoint = endpoint_response.json()
    assert endpoint["simulation_latency_ms"] == 100
    assert endpoint["simulation_failure_rate"] == 50
    assert endpoint["simulation_timeout_rate"] == 0

    event_response = client.post(
        "/events",
        json={
            "event_type": "test.failure.sim",
            "payload": {"message": "hello"},
        },
    )

    assert event_response.status_code == 201, event_response.text

    deliveries_response = client.get("/deliveries")

    assert deliveries_response.status_code == 200, deliveries_response.text
    deliveries = deliveries_response.json()
    assert len(deliveries) == 1
    assert deliveries[0]["endpoint_id"] == endpoint["id"]
