import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.api.endpoints.users import get_db as get_db_users
from app.api.endpoints.auth import get_db as get_db_auth
from app.api.endpoints.tasks import get_db as get_db_tasks
from app.api.endpoints.applications import get_db as get_db_applications
from app.api.endpoints.admin import get_db as get_db_admin

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop the tables after the test
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Override all get_db dependencies
    app.dependency_overrides[get_db_users] = override_get_db
    app.dependency_overrides[get_db_auth] = override_get_db
    app.dependency_overrides[get_db_tasks] = override_get_db
    app.dependency_overrides[get_db_applications] = override_get_db
    app.dependency_overrides[get_db_admin] = override_get_db

    with TestClient(app) as c:
        yield c

    # Clear overrides after test
    app.dependency_overrides.clear()
