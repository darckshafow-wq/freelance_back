"""
Tests d'authentification : inscription et connexion.
"""
from fastapi.testclient import TestClient
from tests.conftest import create_user, auth_headers


def test_register_user(client: TestClient):
    """Un nouvel utilisateur peut s'inscrire."""
    r = client.post("/api/v1/users/", json={
        "email": "newuser@test.com",
        "password": "securepass123",
        "full_name": "New User",
        "is_freelancer": True,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "newuser@test.com"
    assert data["is_freelancer"] is True
    assert "hashed_password" not in data


def test_register_duplicate_email(client: TestClient):
    """Deux inscriptions avec le même email doivent échouer."""
    create_user(client, "dup@test.com", "pass123", is_client=True)
    r = client.post("/api/v1/users/", json={
        "email": "dup@test.com",
        "password": "otherpass",
        "full_name": "Dup User",
    })
    assert r.status_code == 400


def test_login_success(client: TestClient):
    """Un utilisateur enregistré peut se connecter et obtenir un token."""
    create_user(client, "login@test.com", "password123", is_client=True)
    r = client.post("/api/v1/login/access-token", data={
        "username": "login@test.com",
        "password": "password123",
    })
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient):
    """Une connexion avec le mauvais mot de passe doit échouer."""
    create_user(client, "badpass@test.com", "correct_pass", is_client=True)
    r = client.post("/api/v1/login/access-token", data={
        "username": "badpass@test.com",
        "password": "wrong_pass",
    })
    assert r.status_code == 400


def test_get_current_user_me(client: TestClient):
    """Un utilisateur authentifié peut récupérer son profil /users/me."""
    create_user(client, "me@test.com", "pass123", is_freelancer=True)
    headers = auth_headers(client, "me@test.com", "pass123")
    r = client.get("/api/v1/users/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == "me@test.com"


def test_access_protected_without_token(client: TestClient):
    """L'accès à une route protégée sans token doit retourner 401."""
    r = client.get("/api/v1/users/me")
    assert r.status_code == 401
