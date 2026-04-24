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
    inactive_response = client.post(
        "/endpoints",
        json={
            "name": "Inactive endpoint",
            "target_url": "https://example.com/inactive",
        },
    )
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
