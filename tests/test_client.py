"""
Tests des fonctionnalités client : gestion des missions et des candidatures.
"""
from fastapi.testclient import TestClient
from tests.conftest import create_user, auth_headers


def test_client_create_task(client: TestClient):
    """Un client peut créer une mission."""
    create_user(client, "client@test.com", "pass123", is_client=True)
    headers = auth_headers(client, "client@test.com", "pass123")

    r = client.post("/api/v1/client/tasks", headers=headers, json={
        "title": "Développeur Python",
        "description": "Développer une API FastAPI",
        "price": 1500.0,
        "location": "Paris",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "Développeur Python"
    assert data["status"] == "pending"


def test_freelancer_cannot_create_task(client: TestClient):
    """Un freelancer ne peut pas créer une mission (403)."""
    create_user(client, "free@test.com", "pass123", is_freelancer=True)
    headers = auth_headers(client, "free@test.com", "pass123")

    r = client.post("/api/v1/client/tasks", headers=headers, json={
        "title": "Task illégitime",
        "price": 100.0,
        "location": "Remote",
    })
    assert r.status_code == 403


def test_client_get_my_tasks(client: TestClient):
    """Un client peut voir ses missions créées."""
    create_user(client, "client@test.com", "pass123", is_client=True)
    headers = auth_headers(client, "client@test.com", "pass123")

    client.post("/api/v1/client/tasks", headers=headers, json={
        "title": "Tâche A", "price": 100.0, "location": "Lyon"
    })
    client.post("/api/v1/client/tasks", headers=headers, json={
        "title": "Tâche B", "price": 200.0, "location": "Remote"
    })

    r = client.get("/api/v1/client/tasks", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    titles = {t["title"] for t in data}
    assert titles == {"Tâche A", "Tâche B"}


def test_client_accept_reject_application(client: TestClient):
    """Un client peut accepter puis rejeter des candidatures."""
    # Setup
    create_user(client, "client@test.com", "pass123", is_client=True)
    create_user(client, "admin@test.com", "pass123", is_admin=True)
    create_user(client, "free@test.com", "pass123", is_freelancer=True)

    client_h = auth_headers(client, "client@test.com", "pass123")
    admin_h = auth_headers(client, "admin@test.com", "pass123")
    free_h = auth_headers(client, "free@test.com", "pass123")

    # Créer + valider tâche
    task_r = client.post("/api/v1/client/tasks", headers=client_h, json={
        "title": "Task pour test accept/reject", "price": 500.0, "location": "Remote"
    })
    task_id = task_r.json()["id"]
    client.put(f"/api/v1/admin/tasks/{task_id}", headers=admin_h,
               json={"title": "Task pour test accept/reject", "price": 500.0, "status": "validated"})

    # Freelancer postule
    app_r = client.post("/api/v1/freelance/apply", headers=free_h, json={
        "task_id": task_id, "message": "Je suis disponible"
    })
    app_id = app_r.json()["id"]

    # Client accepte la candidature
    r = client.put(f"/api/v1/client/applications/{app_id}/accept", headers=client_h)
    assert r.status_code == 200
    assert r.json()["status"] == "accepted"

    # Client peut aussi rejeter
    r = client.put(f"/api/v1/client/applications/{app_id}/reject", headers=client_h)
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


def test_client_view_task_applications(client: TestClient):
    """Un client peut voir les candidatures reçues pour sa mission."""
    create_user(client, "client@test.com", "pass123", is_client=True)
    create_user(client, "admin@test.com", "pass123", is_admin=True)
    create_user(client, "free1@test.com", "pass123", is_freelancer=True)
    create_user(client, "free2@test.com", "pass123", is_freelancer=True)

    client_h = auth_headers(client, "client@test.com", "pass123")
    admin_h = auth_headers(client, "admin@test.com", "pass123")

    task_r = client.post("/api/v1/client/tasks", headers=client_h, json={
        "title": "Multi-candidats", "price": 800.0, "location": "Lyon"
    })
    task_id = task_r.json()["id"]
    client.put(f"/api/v1/admin/tasks/{task_id}", headers=admin_h,
               json={"title": "Multi-candidats", "price": 800.0, "status": "validated"})

    # Les deux freelancers postulent
    for email in ["free1@test.com", "free2@test.com"]:
        h = auth_headers(client, email, "pass123")
        client.post("/api/v1/freelance/apply", headers=h, json={
            "task_id": task_id, "message": f"Candidature de {email}"
        })

    r = client.get(f"/api/v1/client/tasks/{task_id}/applications", headers=client_h)
    assert r.status_code == 200
    assert len(r.json()) == 2
