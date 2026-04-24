from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_endpoint(client: TestClient) -> None:
    response = client.post(
        "/endpoints",
        json={
            "name": "Local test endpoint",
            "target_url": "https://example.com/webhook",
            "simulation_latency_ms": 100,
            "simulation_failure_rate": 50,
            "simulation_timeout_rate": 0,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["name"] == "Local test endpoint"
    assert body["target_url"] == "https://example.com/webhook"
    assert body["is_active"] is True
    assert body["simulation_latency_ms"] == 100
    assert body["simulation_failure_rate"] == 50
    assert body["simulation_timeout_rate"] == 0


def test_patch_endpoint_updates_status_and_simulation_config(client: TestClient) -> None:
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
        json={
            "is_active": False,
            "simulation_latency_ms": 250,
            "simulation_failure_rate": 25,
            "simulation_timeout_rate": 10,
        },
    )

    assert patch_response.status_code == 200
    patched_endpoint = patch_response.json()
    assert patched_endpoint["is_active"] is False
    assert patched_endpoint["simulation_latency_ms"] == 250
    assert patched_endpoint["simulation_failure_rate"] == 25
    assert patched_endpoint["simulation_timeout_rate"] == 10

    list_response = client.get("/endpoints")

    assert list_response.status_code == 200
    endpoints = list_response.json()
    assert len(endpoints) == 1
    assert endpoints[0]["id"] == endpoint_id
    assert endpoints[0]["is_active"] is False
    assert endpoints[0]["simulation_latency_ms"] == 250
    assert endpoints[0]["simulation_failure_rate"] == 25
    assert endpoints[0]["simulation_timeout_rate"] == 10


def test_create_endpoint_rejects_invalid_simulation_values(client: TestClient) -> None:
    invalid_payloads = [
        {
            "name": "Bad latency",
            "target_url": "https://example.com/webhook",
            "simulation_latency_ms": -1,
        },
        {
            "name": "Bad failure rate high",
            "target_url": "https://example.com/webhook",
            "simulation_failure_rate": 101,
        },
        {
            "name": "Bad failure rate low",
            "target_url": "https://example.com/webhook",
            "simulation_failure_rate": -1,
        },
        {
            "name": "Bad timeout rate high",
            "target_url": "https://example.com/webhook",
            "simulation_timeout_rate": 101,
        },
        {
            "name": "Bad timeout rate low",
            "target_url": "https://example.com/webhook",
            "simulation_timeout_rate": -1,
        },
    ]

    for payload in invalid_payloads:
        response = client.post("/endpoints", json=payload)
        assert response.status_code == 422


def test_patch_endpoint_rejects_invalid_simulation_values(client: TestClient) -> None:
    create_response = client.post(
        "/endpoints",
        json={
            "name": "Validation target",
            "target_url": "https://example.com/webhook",
        },
    )
    endpoint_id = create_response.json()["id"]

    invalid_payloads = [
        {"simulation_latency_ms": -1},
        {"simulation_failure_rate": -1},
        {"simulation_failure_rate": 101},
        {"simulation_timeout_rate": -1},
        {"simulation_timeout_rate": 101},
    ]

    for payload in invalid_payloads:
        response = client.patch(f"/endpoints/{endpoint_id}", json=payload)
        assert response.status_code == 422
