from __future__ import annotations

import uuid

from fastapi.testclient import TestClient


def test_replay_creates_new_delivery(client: TestClient) -> None:
    endpoint_response = client.post(
        "/endpoints",
        json={
            "name": "Replay endpoint",
            "target_url": "https://example.com/webhook",
        },
    )
    assert endpoint_response.status_code == 201

    event_response = client.post(
        "/events",
        json={
            "event_type": "replay.test",
            "payload": {"message": "hello"},
        },
    )
    assert event_response.status_code == 201

    deliveries_response = client.get("/deliveries")
    assert deliveries_response.status_code == 200
    original_delivery = deliveries_response.json()[0]

    replay_response = client.post(f"/deliveries/{original_delivery['id']}/replay")

    assert replay_response.status_code == 200
    replayed_delivery = replay_response.json()
    assert replayed_delivery["id"] != original_delivery["id"]
    assert replayed_delivery["event_id"] == original_delivery["event_id"]
    assert replayed_delivery["endpoint_id"] == original_delivery["endpoint_id"]
    assert replayed_delivery["status"] == "pending"
    assert replayed_delivery["total_attempts"] == 0
    assert replayed_delivery["last_error"] is None
    assert replayed_delivery["attempts"] == []


def test_replay_missing_delivery_returns_404(client: TestClient) -> None:
    response = client.post(f"/deliveries/{uuid.uuid4()}/replay")

    assert response.status_code == 404
    assert response.json() == {"detail": "Delivery not found"}
