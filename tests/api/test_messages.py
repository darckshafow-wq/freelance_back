import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_send_message():
    # Because we mocked get_current_user_mock to return user with ID=1,
    # we can just send the request directly. User ID 1 is the Admin.
    response = client.post(
        "/api/v1/messages/",
        json={
            "content": "Hello, this is a test message",
            "receiver_id": 2
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Hello, this is a test message"
    assert data["sender_id"] == 1
    assert data["receiver_id"] == 2
