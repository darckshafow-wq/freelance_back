from fastapi.testclient import TestClient
from tests.conftest import auth_headers, create_user


def test_send_message(client: TestClient):
    sender = create_user(
        client,
        "admin@test.com",
        "password123",
        full_name="Test Admin",
        is_admin=True,
    )
    receiver = create_user(
        client,
        "receiver@test.com",
        "password123",
        full_name="Receiver User",
    )
    headers = auth_headers(client, "admin@test.com", "password123")

    response = client.post(
        "/api/v1/messages/",
        headers=headers,
        json={
            "content": "Hello, this is a test message",
            "receiver_id": receiver["id"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Hello, this is a test message"
    assert data["sender_id"] == sender["id"]
    assert data["receiver_id"] == receiver["id"]
