from fastapi.testclient import TestClient
from app.models.task import TaskStatus

def get_auth_token(client: TestClient, email: str, password: str) -> str:
    response = client.post(
        "/api/v1/login/access-token",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]

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
    # 400 means already exists from a previous run, which is fine
    assert response.status_code in (200, 400)
    if response.status_code == 200:
        data = response.json()
        assert data["email"] == "freelance@test.com"

def test_create_task(client: TestClient):
    # Ensure client user exists
    client.post(
        "/api/v1/users/",
        json={
            "email": "client@test.com",
            "password": "password123",
            "full_name": "Test Client",
            "is_client": True,
        },
    )
    token = get_auth_token(client, "client@test.com", "password123")
    
    # Create a task
    response = client.post(
        "/api/v1/tasks/",
        headers={"Authorization": f"Bearer {token}"},
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
    # Ensure admin user exists
    client.post(
        "/api/v1/users/",
        json={
            "email": "admin@test.com",
            "password": "password123",
            "full_name": "Test Admin",
            "is_admin": True,
        },
    )
    # And a client
    client.post(
        "/api/v1/users/",
        json={
            "email": "client@test.com",
            "password": "password123",
            "full_name": "Test Client",
            "is_client": True,
        },
    )
    token = get_auth_token(client, "client@test.com", "password123")
    
    # First create a task
    post_resp = client.post(
        "/api/v1/tasks/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Task to Validate",
            "price": 100.0,
            "location": "Paris"
        },
    )
    task_id = post_resp.json()["id"]

    # Admin updates the task
    admin_token = get_auth_token(client, "admin@test.com", "password123")
    update_resp = client.put(
        f"/api/v1/admin/tasks/{task_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Task to Validate",
            "price": 100.0,
            "status": TaskStatus.VALIDATED
        }
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == TaskStatus.VALIDATED
