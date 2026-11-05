import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.database.base import Base
from backend.app.database.connection import get_db


# Separate in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)


# Create test database tables
Base.metadata.create_all(bind=test_engine)


# Override the production database dependency
def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=test_engine)

# TEST 1: Home endpoint
def test_home(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["project"] == "DocuMind AI"


# TEST 2: Health endpoint
def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# TEST 3: Project information
def test_project_info(client):
    response = client.get("/api/v1/info")

    assert response.status_code == 200
    assert response.json()["project_name"] == "DocuMind AI"
    assert len(response.json()["agents"]) == 3

def test_create_workflow(client):
    response = client.post(
        "/api/v1/workflows/",
        json={
            "title": "Automated Test Workflow",
            "description": "Testing workflow creation"
        }
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Automated Test Workflow"
    assert response.json()["status"] == "PENDING"

def test_get_all_workflows(client):
    client.post(
        "/api/v1/workflows/",
        json={
            "title": "Workflow One",
            "description": "First workflow"
        }
    )

    client.post(
        "/api/v1/workflows/",
        json={
            "title": "Workflow Two",
            "description": "Second workflow"
        }
    )

    response = client.get("/api/v1/workflows/")

    assert response.status_code == 200
    assert len(response.json()) == 2

def test_get_workflow_by_id(client):
    create_response = client.post(
        "/api/v1/workflows/",
        json={
            "title": "Find Me",
            "description": "Testing retrieval"
        }
    )

    workflow_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/workflows/{workflow_id}"
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Find Me"

def test_update_workflow(client):
    create_response = client.post(
        "/api/v1/workflows/",
        json={
            "title": "Update Test",
            "description": "Before update"
        }
    )

    workflow_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/workflows/{workflow_id}",
        json={
            "status": "RUNNING"
        }
    )

    assert response.status_code == 200
    assert response.json()["status"] == "RUNNING"

def test_delete_workflow(client):
    create_response = client.post(
        "/api/v1/workflows/",
        json={
            "title": "Delete Test",
            "description": "Testing deletion"
        }
    )

    workflow_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/workflows/{workflow_id}"
    )

    assert response.status_code == 204

def test_get_deleted_workflow(client):
    create_response = client.post(
        "/api/v1/workflows/",
        json={
            "title": "Deleted Workflow",
            "description": "Testing 404 response"
        }
    )

    workflow_id = create_response.json()["id"]

    client.delete(
        f"/api/v1/workflows/{workflow_id}"
    )

    response = client.get(
        f"/api/v1/workflows/{workflow_id}"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Workflow not found"

def test_get_nonexistent_workflow(client):
    response = client.get("/api/v1/workflows/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Workflow not found"

def test_create_workflow_without_title(client):
    response = client.post(
        "/api/v1/workflows/",
        json={
            "description": "Workflow without a title"
        }
    )

    assert response.status_code == 422