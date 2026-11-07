import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.database.base import Base
from backend.app.database.connection import get_db
from backend.app.models import Document, Workflow
from backend.tests.conftest import (
    apply_test_auth_override,
)


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

    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    previous_overrides = app.dependency_overrides.copy()

    app.dependency_overrides[get_db] = override_get_db
    apply_test_auth_override()

    try:
        with TestClient(app) as test_client:
            yield test_client

    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)

        Base.metadata.drop_all(bind=test_engine)


# =========================================
# TEST DATA HELPER
# =========================================

def create_test_document():

    db = TestingSessionLocal()

    try:
        workflow = Workflow(
            title="Document Approval Test",
            description="Testing document approval workflow"
        )

        db.add(workflow)
        db.flush()

        document = Document(
            workflow_id=workflow.id,
            title="Test Documentation",
            document_type="MARKDOWN",
            content="# Test Documentation"
        )

        db.add(document)
        db.commit()

        db.refresh(document)

        document_id = document.id
        workflow_id = workflow.id

        return document_id, workflow_id

    finally:
        db.close()


# =========================================
# DOCUMENT RETRIEVAL TESTS
# =========================================

def test_get_document(client):

    document_id, workflow_id = create_test_document()

    response = client.get(
        f"/api/v1/documents/{document_id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == document_id
    assert response.json()["workflow_id"] == workflow_id
    assert response.json()["approval_status"] == "PENDING"


def test_get_nonexistent_document(client):

    response = client.get("/api/v1/documents/9999")

    assert response.status_code == 404


# =========================================
# DOCUMENT APPROVAL TESTS
# =========================================

def test_approve_document(client):

    document_id, workflow_id = create_test_document()

    response = client.post(
        f"/api/v1/documents/{document_id}/approve",
        json={
            "reviewed_by": "Project Admin"
        }
    )

    assert response.status_code == 200
    assert response.json()["approval_status"] == "APPROVED"
    assert response.json()["reviewed_by"] == "Project Admin"
    assert response.json()["reviewed_at"] is not None
    assert response.json()["approval_reason"] is None


def test_approve_document_updates_workflow(client):

    document_id, workflow_id = create_test_document()

    response = client.post(
        f"/api/v1/documents/{document_id}/approve",
        json={
            "reviewed_by": "Project Admin"
        }
    )

    assert response.status_code == 200

    workflow_response = client.get(
        f"/api/v1/workflows/{workflow_id}"
    )

    assert workflow_response.status_code == 200
    assert workflow_response.json()["status"] == "APPROVED"


def test_prevent_duplicate_approval(client):

    document_id, _ = create_test_document()

    approval_data = {
        "reviewed_by": "Project Admin"
    }

    first_response = client.post(
        f"/api/v1/documents/{document_id}/approve",
        json=approval_data
    )

    second_response = client.post(
        f"/api/v1/documents/{document_id}/approve",
        json=approval_data
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409


# =========================================
# DOCUMENT REJECTION TESTS
# =========================================

def test_reject_document(client):

    document_id, workflow_id = create_test_document()

    response = client.post(
        f"/api/v1/documents/{document_id}/reject",
        json={
            "reviewed_by": "Project Admin",
            "reason": "Documentation requires additional technical details."
        }
    )

    assert response.status_code == 200
    assert response.json()["approval_status"] == "REJECTED"
    assert response.json()["reviewed_by"] == "Project Admin"
    assert response.json()["reviewed_at"] is not None
    assert response.json()["approval_reason"] == (
        "Documentation requires additional technical details."
    )


def test_reject_document_updates_workflow(client):

    document_id, workflow_id = create_test_document()

    response = client.post(
        f"/api/v1/documents/{document_id}/reject",
        json={
            "reviewed_by": "Project Admin",
            "reason": "Documentation needs corrections."
        }
    )

    assert response.status_code == 200

    workflow_response = client.get(
        f"/api/v1/workflows/{workflow_id}"
    )

    assert workflow_response.status_code == 200
    assert workflow_response.json()["status"] == "REJECTED"


def test_prevent_duplicate_rejection(client):

    document_id, _ = create_test_document()

    rejection_data = {
        "reviewed_by": "Project Admin",
        "reason": "Documentation needs corrections."
    }

    first_response = client.post(
        f"/api/v1/documents/{document_id}/reject",
        json=rejection_data
    )

    second_response = client.post(
        f"/api/v1/documents/{document_id}/reject",
        json=rejection_data
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409


# =========================================
# CROSS-REVIEW PROTECTION TESTS
# =========================================

def test_cannot_reject_approved_document(client):

    document_id, _ = create_test_document()

    client.post(
        f"/api/v1/documents/{document_id}/approve",
        json={
            "reviewed_by": "Project Admin"
        }
    )

    response = client.post(
        f"/api/v1/documents/{document_id}/reject",
        json={
            "reviewed_by": "Project Admin",
            "reason": "Trying to reject an approved document."
        }
    )

    assert response.status_code == 409


def test_cannot_approve_rejected_document(client):

    document_id, _ = create_test_document()

    client.post(
        f"/api/v1/documents/{document_id}/reject",
        json={
            "reviewed_by": "Project Admin",
            "reason": "Documentation needs corrections."
        }
    )

    response = client.post(
        f"/api/v1/documents/{document_id}/approve",
        json={
            "reviewed_by": "Project Admin"
        }
    )

    assert response.status_code == 409


# =========================================
# REQUEST VALIDATION TESTS
# =========================================

def test_approve_without_reviewer_uses_principal(client):

    document_id, _ = create_test_document()

    response = client.post(
        f"/api/v1/documents/{document_id}/approve",
        json={}
    )

    assert response.status_code == 200
    assert response.json()["approval_status"] == "APPROVED"
    assert response.json()["reviewed_by"] == "Project Admin"


def test_reject_with_short_reason(client):

    document_id, _ = create_test_document()

    response = client.post(
        f"/api/v1/documents/{document_id}/reject",
        json={
            "reviewed_by": "Project Admin",
            "reason": "Bad"
        }
    )

    assert response.status_code == 422

# =========================================
# WORKFLOW FAILURE STATUS PROTECTION TESTS
# =========================================

def test_approve_document_preserves_partial_workflow_status(client):

    document_id, workflow_id = create_test_document()

    # Set the workflow status to PARTIAL.
    db = TestingSessionLocal()

    try:
        workflow = db.query(Workflow).filter(
            Workflow.id == workflow_id
        ).first()

        workflow.status = "PARTIAL"
        db.commit()

    finally:
        db.close()

    # Approve the document.
    response = client.post(
        f"/api/v1/documents/{document_id}/approve",
        json={
            "reviewed_by": "Project Admin"
        }
    )

    assert response.status_code == 200
    assert response.json()["approval_status"] == "APPROVED"

    # Verify that PARTIAL status is preserved.
    workflow_response = client.get(
        f"/api/v1/workflows/{workflow_id}"
    )

    assert workflow_response.status_code == 200
    assert workflow_response.json()["status"] == "PARTIAL"


def test_reject_document_preserves_failed_workflow_status(client):

    document_id, workflow_id = create_test_document()

    # Set the workflow status to FAILED.
    db = TestingSessionLocal()

    try:
        workflow = db.query(Workflow).filter(
            Workflow.id == workflow_id
        ).first()

        workflow.status = "FAILED"
        db.commit()

    finally:
        db.close()

    # Reject the document.
    response = client.post(
        f"/api/v1/documents/{document_id}/reject",
        json={
            "reviewed_by": "Project Admin",
            "reason": "Documentation requires additional technical details."
        }
    )

    assert response.status_code == 200
    assert response.json()["approval_status"] == "REJECTED"

    # Verify that FAILED status is preserved.
    workflow_response = client.get(
        f"/api/v1/workflows/{workflow_id}"
    )

    assert workflow_response.status_code == 200
    assert workflow_response.json()["status"] == "FAILED"

# =========================================
# WHITESPACE VALIDATION TESTS
# =========================================

def test_approve_ignores_whitespace_client_reviewed_by(client):

    document_id, _ = create_test_document()

    response = client.post(
        f"/api/v1/documents/{document_id}/approve",
        json={"reviewed_by": "   "}
    )

    assert response.status_code == 200
    assert response.json()["reviewed_by"] == "Project Admin"


def test_approve_ignores_client_reviewed_by_value(client):

    document_id, _ = create_test_document()

    response = client.post(
        f"/api/v1/documents/{document_id}/approve",
        json={"reviewed_by": "  Someone Else  "}
    )

    assert response.status_code == 200
    assert response.json()["reviewed_by"] == "Project Admin"


def test_reject_rejects_whitespace_reason(client):

    document_id, _ = create_test_document()

    response = client.post(
        f"/api/v1/documents/{document_id}/reject",
        json={
            "reviewed_by": "Project Admin",
            "reason": "     "
        }
    )

    assert response.status_code == 422


def test_reject_uses_principal_and_trims_reason(client):

    document_id, _ = create_test_document()

    response = client.post(
        f"/api/v1/documents/{document_id}/reject",
        json={
            "reviewed_by": "  Someone Else  ",
            "reason": "  Needs more technical details  "
        }
    )

    assert response.status_code == 200
    assert response.json()["reviewed_by"] == "Project Admin"
    assert response.json()["approval_reason"] == (
        "Needs more technical details"
    )