from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_endpoint(client: TestClient) -> None:
    response = client.post(
        "/endpoints",
        json={
            "name": "Local test endpoint",
            "target_url": "https://example.com/webhook",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["name"] == "Local test endpoint"
    assert body["target_url"] == "https://example.com/webhook"
    assert body["is_active"] is True


def test_patch_endpoint_deactivates_endpoint(client: TestClient) -> None:
    create_response = client.post(
        "/endpoints",
        json={
            "name": "Deactivate me",
            "target_url": "https://example.com/webhook",
        },
    )
    endpoint_id = create_response.json()["id"]

    patch_response = client.patch(
        f"/endpoints/{endpoint_id}",
        json={"is_active": False},
    )

    assert patch_response.status_code == 200
    assert patch_response.json()["is_active"] is False

    list_response = client.get("/endpoints")

    assert list_response.status_code == 200
    endpoints = list_response.json()
    assert len(endpoints) == 1
    assert endpoints[0]["id"] == endpoint_id
    assert endpoints[0]["is_active"] is False
