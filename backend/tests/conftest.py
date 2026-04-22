"""
pytest conftest.py — shared fixtures for all tests.
Uses an in-memory SQLite DB so no PostgreSQL is needed for unit tests.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Override settings BEFORE importing app
import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-unit-tests-only"
os.environ["GEMINI_API_KEY"] = ""
os.environ["APP_ENV"] = "test"

from config.database import Base, get_db
from main import app

# ─── In-Memory SQLite Engine ─────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Create all tables once for the test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    """Provide a transactional test DB session, rolled back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    """FastAPI test client with DB override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def registered_user(client):
    """Register and return a test user."""
    res = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "Test@1234",
        "business_name": "Test Co",
    })
    assert res.status_code == 201
    return res.json()


@pytest.fixture
def auth_headers(client, registered_user):
    """Return Authorization headers for the test user."""
    res = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "Test@1234",
    })
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_transaction_payload():
    """A valid transaction creation payload."""
    return {
        "description": "Test software services",
        "amount": 50000,
        "transaction_type": "income",
        "transaction_date": "2024-11-01",
        "gst_type": "CGST",
        "gst_rate": 18,
        "party_name": "Client Corp",
        "invoice_number": "INV-TEST-001",
    }
