"""
conftest.py – Configuration de test centralisée.

Utilise une base de données SQLite en mémoire avec StaticPool pour s'assurer
que toutes les dépendances partagent la même connexion.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.api.deps import get_db

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# ─── Helpers réutilisables ────────────────────────────────────────────────────

def create_user(client: TestClient, email: str, password: str, **kwargs) -> dict:
    """Crée un utilisateur et retourne la réponse JSON."""
    payload = {"email": email, "password": password, "full_name": "Test User", **kwargs}
    r = client.post("/api/v1/users/", json=payload)
    assert r.status_code == 200, f"create_user failed: {r.json()}"
    return r.json()


def get_auth_token(client: TestClient, email: str, password: str) -> str:
    """Authentifie un utilisateur et retourne son token JWT."""
    r = client.post("/api/v1/login/access-token", data={"username": email, "password": password})
    assert r.status_code == 200, f"login failed: {r.json()}"
    return r.json()["access_token"]


def auth_headers(client: TestClient, email: str, password: str) -> dict:
    """Retourne les headers d'authentification Bearer."""
    token = get_auth_token(client, email, password)
    return {"Authorization": f"Bearer {token}"}
