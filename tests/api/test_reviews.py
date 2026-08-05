from fastapi.testclient import TestClient
from tests.conftest import auth_headers, create_user


def test_create_review(client: TestClient):
    create_user(
        client,
        "reviewer@test.com",
        "password123",
        full_name="Review User",
    )
    headers = auth_headers(client, "reviewer@test.com", "password123")

    response = client.post(
        "/api/v1/reviews/",
        headers=headers,
        json={
            "content": "Test review content",
            "review_type": "suggestion",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Test review content"
    assert data["review_type"] == "suggestion"
