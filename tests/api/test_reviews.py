import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_review():
    response = client.post(
        "/api/v1/reviews/",
        json={
            "content": "Test review content",
            "review_type": "suggestion"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Test review content"
    assert data["review_type"] == "suggestion"
