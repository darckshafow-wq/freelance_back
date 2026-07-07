from fastapi.testclient import TestClient
from app.models.task import TaskStatus

def test_create_user(client: TestClient):
    response = client.post(
        "/api/v1/users/",
        json={
            "email": "freelance@test.com",
            "password": "password123",
            "full_name": "Test Freelancer",
            "is_freelancer": True,
            "location": "Paris"
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "freelance@test.com"
    assert data["is_freelancer"] == True

def test_create_task(client: TestClient):
    # Create a task (simulate client)
    response = client.post(
        "/api/v1/tasks/",
        json={
            "title": "Need a React developer",
            "description": "Fix my website",
            "price": 500.0,
            "location": "Remote"
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Need a React developer"
    assert data["status"] == TaskStatus.PENDING

def test_admin_validate_task(client: TestClient):
    # First create a task
    post_resp = client.post(
        "/api/v1/tasks/",
        json={
            "title": "Task to Validate",
            "price": 100.0,
            "location": "Paris"
        },
    )
    task_id = post_resp.json()["id"]

    # Admin updates the task
    update_resp = client.put(
        f"/api/v1/admin/tasks/{task_id}",
        json={
            "title": "Task to Validate",
            "price": 100.0,
            "status": TaskStatus.VALIDATED
        }
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == TaskStatus.VALIDATED
