import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.auth import get_current_principal
from backend.app.auth.config import AuthSettings
from backend.app.database.base import Base
from backend.app.database.connection import get_db
from backend.app.main import app
from backend.app.models import Document, Workflow


TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def auth_client(monkeypatch):
    """
    HTTP client that exercises the real auth dependency.
    Does not override get_current_principal.
    """

    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides.pop(get_current_principal, None)
    app.dependency_overrides[get_db] = override_get_db

    monkeypatch.setenv("DOCU_MIND_ENV", "production")
    monkeypatch.setenv(
        "DOCU_MIND_API_KEYS",
        "test-secret-key-one",
    )
    monkeypatch.setenv(
        "DOCU_MIND_API_KEY_NAMES",
        "Project Admin",
    )

    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
        Base.metadata.drop_all(bind=test_engine)


def create_pending_document():
    db = TestingSessionLocal()

    try:
        workflow = Workflow(
            title="Auth Review Workflow",
            description="Auth tests",
        )
        db.add(workflow)
        db.flush()

        document = Document(
            workflow_id=workflow.id,
            title="Auth Doc",
            document_type="MARKDOWN",
            content="# Auth Doc",
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        return document.id
    finally:
        db.close()


def test_health_is_public():
    previous = app.dependency_overrides.copy()
    app.dependency_overrides.pop(get_current_principal, None)

    try:
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


def test_root_and_info_are_public():
    previous = app.dependency_overrides.copy()
    app.dependency_overrides.pop(get_current_principal, None)

    try:
        with TestClient(app) as client:
            assert client.get("/").status_code == 200
            assert client.get("/api/v1/info").status_code == 200
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


def test_protected_endpoint_missing_credentials(auth_client):
    response = auth_client.get("/api/v1/workflows/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required."


def test_protected_endpoint_malformed_scheme(auth_client):
    response = auth_client.get(
        "/api/v1/workflows/",
        headers={"Authorization": "Token test-secret-key-one"},
    )
    assert response.status_code == 401


def test_protected_endpoint_empty_bearer(auth_client):
    response = auth_client.get(
        "/api/v1/workflows/",
        headers={"Authorization": "Bearer "},
    )
    assert response.status_code == 401


def test_protected_endpoint_invalid_token(auth_client):
    response = auth_client.get(
        "/api/v1/workflows/",
        headers={"Authorization": "Bearer wrong-key"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid authentication credentials."
    )


def test_protected_endpoint_valid_token(auth_client):
    response = auth_client.get(
        "/api/v1/workflows/",
        headers={"Authorization": "Bearer test-secret-key-one"},
    )
    assert response.status_code == 200
    assert response.json() == []


def test_auth_not_configured_returns_503(monkeypatch):
    previous = app.dependency_overrides.copy()
    app.dependency_overrides.pop(get_current_principal, None)

    monkeypatch.setenv("DOCU_MIND_ENV", "production")
    monkeypatch.delenv("DOCU_MIND_API_KEYS", raising=False)
    monkeypatch.delenv("DOCU_MIND_API_KEY_NAMES", raising=False)

    # Ensure get_auth_settings sees empty keys even if .env loaded values.
    monkeypatch.setattr(
        "backend.app.auth.dependencies.get_auth_settings",
        lambda: AuthSettings(
            api_keys=(),
            key_labels=(),
            environment="production",
        ),
    )

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/workflows/",
                headers={"Authorization": "Bearer anything"},
            )
            assert response.status_code == 503
            assert response.json()["detail"] == (
                "Authentication is not configured."
            )
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


def test_approve_uses_principal_not_client_reviewed_by(auth_client):
    document_id = create_pending_document()

    response = auth_client.post(
        f"/api/v1/documents/{document_id}/approve",
        headers={"Authorization": "Bearer test-secret-key-one"},
        json={"reviewed_by": "Forged Reviewer Name"},
    )

    assert response.status_code == 200
    assert response.json()["approval_status"] == "APPROVED"
    assert response.json()["reviewed_by"] == "Project Admin"


def test_reject_uses_principal_not_client_reviewed_by(auth_client):
    document_id = create_pending_document()

    response = auth_client.post(
        f"/api/v1/documents/{document_id}/reject",
        headers={"Authorization": "Bearer test-secret-key-one"},
        json={
            "reviewed_by": "Forged Reviewer Name",
            "reason": "Needs more technical detail in the summary.",
        },
    )

    assert response.status_code == 200
    assert response.json()["approval_status"] == "REJECTED"
    assert response.json()["reviewed_by"] == "Project Admin"
