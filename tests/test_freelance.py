"""
Tests des fonctionnalités freelancer : candidatures et statistiques.
"""
from fastapi.testclient import TestClient
from tests.conftest import create_user, auth_headers


def _setup_validated_task(client: TestClient) -> dict:
    """Helper: crée un client + une tâche validée par un admin, retourne la tâche."""
    # Créer le client
    create_user(client, "client@test.com", "pass123", is_client=True)
    # Créer l'admin
    create_user(client, "admin@test.com", "pass123", is_admin=True)

    client_headers = auth_headers(client, "client@test.com", "pass123")
    admin_headers = auth_headers(client, "admin@test.com", "pass123")

    # Créer la tâche (statut PENDING par défaut)
    task_r = client.post("/api/v1/client/tasks", headers=client_headers, json={
        "title": "Développeur React Senior",
        "description": "Refonte complète d'une webapp",
        "price": 2500.0,
        "location": "Remote",
    })
    assert task_r.status_code == 200
    task = task_r.json()

    # Valider la tâche (admin)
    validate_r = client.put(
        f"/api/v1/admin/tasks/{task['id']}",
        headers=admin_headers,
        json={"title": task["title"], "price": task["price"], "status": "validated"},
    )
    assert validate_r.status_code == 200
    return validate_r.json()


def test_freelancer_apply_for_task(client: TestClient):
    """Un freelancer peut postuler à une tâche validée."""
    task = _setup_validated_task(client)
    create_user(client, "free@test.com", "pass123", is_freelancer=True)
    headers = auth_headers(client, "free@test.com", "pass123")

    r = client.post("/api/v1/freelance/apply", headers=headers, json={
        "task_id": task["id"],
        "message": "Je suis très motivé pour ce projet!",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["task_id"] == task["id"]
    assert data["status"] == "pending"


def test_freelancer_cannot_apply_twice(client: TestClient):
    """Un freelancer ne peut pas postuler deux fois à la même tâche."""
    task = _setup_validated_task(client)
    create_user(client, "free@test.com", "pass123", is_freelancer=True)
    headers = auth_headers(client, "free@test.com", "pass123")

    payload = {"task_id": task["id"], "message": "Première candidature"}
    client.post("/api/v1/freelance/apply", headers=headers, json=payload)

    r = client.post("/api/v1/freelance/apply", headers=headers, json=payload)
    assert r.status_code == 409


def test_freelancer_get_applications(client: TestClient):
    """Un freelancer peut voir ses candidatures."""
    task = _setup_validated_task(client)
    create_user(client, "free@test.com", "pass123", is_freelancer=True)
    headers = auth_headers(client, "free@test.com", "pass123")

    client.post("/api/v1/freelance/apply", headers=headers, json={
        "task_id": task["id"], "message": "Candidature test"
    })

    r = client.get("/api/v1/freelance/applications", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["task_id"] == task["id"]
    assert data[0]["status"] == "pending"


def test_freelancer_get_applications_filtered(client: TestClient):
    """Le filtrage par statut fonctionne correctement."""
    task = _setup_validated_task(client)
    create_user(client, "free@test.com", "pass123", is_freelancer=True)
    headers = auth_headers(client, "free@test.com", "pass123")

    client.post("/api/v1/freelance/apply", headers=headers, json={
        "task_id": task["id"], "message": "Test"
    })

    # Filtrer par statut pending
    r = client.get("/api/v1/freelance/applications?status=pending", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 1

    # Filtrer par statut accepted (aucun résultat)
    r = client.get("/api/v1/freelance/applications?status=accepted", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 0


def test_client_cannot_apply(client: TestClient):
    """Un utilisateur client ne peut pas postuler (403 Forbidden)."""
    task = _setup_validated_task(client)
    headers = auth_headers(client, "client@test.com", "pass123")

    r = client.post("/api/v1/freelance/apply", headers=headers, json={
        "task_id": task["id"], "message": "Je suis client mais je tente"
    })
    assert r.status_code == 403


def test_freelancer_stats(client: TestClient):
    """Les statistiques d'un freelancer retournent la bonne structure."""
    create_user(client, "free@test.com", "pass123", is_freelancer=True)
    headers = auth_headers(client, "free@test.com", "pass123")

    r = client.get("/api/v1/freelance/stats", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "applications_sent" in data
    assert "applications_accepted" in data
    assert "success_rate" in data
    assert data["applications_sent"] == 0
