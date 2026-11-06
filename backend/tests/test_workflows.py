
from datetime import datetime, timezone

import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.database.base import Base
from backend.app.database.connection import get_db
from backend.app.models import AgentLog, Document


# =========================================
# TEST DATABASE CONFIGURATION
# =========================================

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


# =========================================
# DATABASE DEPENDENCY OVERRIDE
# =========================================

def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


# =========================================
# TEST CLIENT FIXTURE
# =========================================

@pytest.fixture
def client():

    # Reset database before every test.
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    # Preserve existing dependency overrides.
    previous_overrides = app.dependency_overrides.copy()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client

    finally:
        # Restore original dependency overrides.
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)

        # Clean up test database.
        Base.metadata.drop_all(bind=test_engine)


# =========================================
# GENERAL API TESTS
# =========================================

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


# =========================================
# WORKFLOW CRUD TESTS
# =========================================

# TEST 4: Create workflow
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


# TEST 5: Get all workflows
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


# TEST 6: Get workflow by ID
def test_get_workflow_by_id(client):

    create_response = client.post(
        "/api/v1/workflows/",
        json={
            "title": "Find Me",
            "description": "Testing retrieval"
        }
    )

    assert create_response.status_code == 201

    workflow_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/workflows/{workflow_id}"
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Find Me"


# TEST 7: Update workflow
def test_update_workflow(client):

    create_response = client.post(
        "/api/v1/workflows/",
        json={
            "title": "Update Test",
            "description": "Before update"
        }
    )

    assert create_response.status_code == 201

    workflow_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/workflows/{workflow_id}",
        json={
            "status": "RUNNING"
        }
    )

    assert response.status_code == 200
    assert response.json()["status"] == "RUNNING"


# TEST 8: Delete workflow
def test_delete_workflow(client):

    create_response = client.post(
        "/api/v1/workflows/",
        json={
            "title": "Delete Test",
            "description": "Testing deletion"
        }
    )

    assert create_response.status_code == 201

    workflow_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/workflows/{workflow_id}"
    )

    assert response.status_code == 204


# TEST 9: Get deleted workflow
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
    assert response.json()["detail"] == "Workflow not found."


# TEST 10: Get nonexistent workflow
def test_get_nonexistent_workflow(client):

    response = client.get(
        "/api/v1/workflows/9999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Workflow not found."


# TEST 11: Create workflow without title
def test_create_workflow_without_title(client):

    response = client.post(
        "/api/v1/workflows/",
        json={
            "description": "Workflow without a title"
        }
    )

    assert response.status_code == 422


# =========================================
# WORKFLOW HISTORY API TESTS
# =========================================

# TEST 12: Get complete workflow history
def test_get_workflow_details(client):

    # Create workflow.
    create_response = client.post(
        "/api/v1/workflows/",
        json={
            "title": "Authentication Review",
            "description": "Testing complete workflow history",
            "source_type": "github_pull_request",
            "source_reference": "demo/repository/pull/2"
        }
    )

    assert create_response.status_code == 201

    workflow_id = create_response.json()["id"]

    # Insert three agent logs and one document.
    db = TestingSessionLocal()

    try:
        # Define a common completion timestamp.
        completed_time = datetime.now(timezone.utc)

        agent_logs = [
            AgentLog(
                workflow_id=workflow_id,
                agent_name="documentation",
                status="COMPLETED",
                input_summary="Documentation input",
                output_summary="Documentation generated",
                completed_at=completed_time
            ),
            AgentLog(
                workflow_id=workflow_id,
                agent_name="code_review",
                status="COMPLETED",
                input_summary="Code review input",
                output_summary="Code review completed",
                completed_at=completed_time
            ),
            AgentLog(
                workflow_id=workflow_id,
                agent_name="team_intelligence",
                status="COMPLETED",
                input_summary="Team intelligence input",
                output_summary="Team summary generated",
                completed_at=completed_time
            )
        ]

        document = Document(
            workflow_id=workflow_id,
            title="Authentication Documentation",
            document_type="MARKDOWN",
            content="# Authentication Documentation"
        )

        db.add_all(agent_logs)
        db.add(document)
        db.commit()

    finally:
        db.close()

    # Retrieve complete workflow history.
    response = client.get(
        f"/api/v1/workflows/{workflow_id}/details"
    )

    assert response.status_code == 200

    data = response.json()

    # Verify workflow information.
    assert data["id"] == workflow_id
    assert data["title"] == "Authentication Review"
    assert data["status"] == "PENDING"

    assert data["source_type"] == "github_pull_request"
    assert data["source_reference"] == "demo/repository/pull/2"

    # Verify timestamps.
    assert data["created_at"] is not None
    assert data["updated_at"] is not None

    # Verify agent logs.
    assert len(data["agent_logs"]) == 3

    agent_names = {
        log["agent_name"]
        for log in data["agent_logs"]
    }

    assert agent_names == {
        "documentation",
        "code_review",
        "team_intelligence"
    }

    for log in data["agent_logs"]:
        assert log["status"] == "COMPLETED"
        assert log["error_message"] is None
        assert log["started_at"] is not None
        assert log["completed_at"] is not None

    # Verify generated document.
    assert len(data["documents"]) == 1

    generated_document = data["documents"][0]

    assert generated_document["title"] == "Authentication Documentation"
    assert generated_document["document_type"] == "MARKDOWN"

    assert (
        generated_document["content"]
        == "# Authentication Documentation"
    )

    assert generated_document["created_at"] is not None


# TEST 13: Workflow history without agent logs or documents
def test_workflow_details_without_agent_logs_or_documents(client):

    create_response = client.post(
        "/api/v1/workflows/",
        json={
            "title": "Empty Workflow",
            "description": "Testing empty workflow history"
        }
    )

    assert create_response.status_code == 201

    workflow_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/workflows/{workflow_id}/details"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == workflow_id
    assert data["agent_logs"] == []
    assert data["documents"] == []


# TEST 14: Workflow history for nonexistent workflow
def test_get_nonexistent_workflow_details(client):

    response = client.get(
        "/api/v1/workflows/9999/details"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Workflow not found."
