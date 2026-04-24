from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient


def test_create_test_webhook_receiver(client: TestClient) -> None:
    response = client.post("/test-webhooks", json={"name": "My test receiver"})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "My test receiver"
    assert body["id"]
    assert body["url"].endswith(f"/test-webhooks/{body['id']}")


def test_post_to_test_webhook_and_list_requests(client: TestClient) -> None:
    create_response = client.post("/test-webhooks", json={"name": "Capture target"})
    receiver = create_response.json()

    post_response = client.post(
        f"/test-webhooks/{receiver['id']}",
        headers={"X-HookHub-Event-Id": "evt_123"},
        json={"message": "hello"},
    )

    assert post_response.status_code == 200
    assert post_response.json() == {"status": "received"}

    requests_response = client.get(f"/test-webhooks/{receiver['id']}/requests")

    assert requests_response.status_code == 200
    requests = requests_response.json()
    assert len(requests) == 1
    assert requests[0]["receiver_id"] == receiver["id"]
    assert requests[0]["method"] == "POST"
    assert requests[0]["body"] == {"message": "hello"}
    assert requests[0]["headers"]["x-hookhub-event-id"] == "evt_123"


def test_missing_test_webhook_receiver_returns_404(client: TestClient) -> None:
    missing_id = uuid4()

    post_response = client.post(f"/test-webhooks/{missing_id}", json={"message": "hello"})
    list_response = client.get(f"/test-webhooks/{missing_id}/requests")

    assert post_response.status_code == 404
    assert list_response.status_code == 404
