from __future__ import annotations

from fastapi.testclient import TestClient


def test_delivery_detail_returns_attempts_array(client: TestClient) -> None:
    endpoint_response = client.post(
        "/endpoints",
        json={
            "name": "Delivery endpoint",
            "target_url": "https://example.com/webhook",
        },
    )
    assert endpoint_response.status_code == 201

    event_response = client.post(
        "/events",
        json={
            "event_type": "delivery.test",
            "payload": {"message": "hello"},
        },
    )
    assert event_response.status_code == 201

    deliveries_response = client.get("/deliveries")

    assert deliveries_response.status_code == 200
    deliveries = deliveries_response.json()
    assert len(deliveries) == 1

    delivery_id = deliveries[0]["id"]
    detail_response = client.get(f"/deliveries/{delivery_id}")

    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["id"] == delivery_id
    assert detail["event_id"] == event_response.json()["id"]
    assert detail["endpoint_id"] == endpoint_response.json()["id"]
    assert detail["attempts"] == []
