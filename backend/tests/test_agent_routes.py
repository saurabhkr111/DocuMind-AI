import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.routes import agents
from backend.app.database.base import Base
from backend.app.database.connection import get_db
from backend.app.models import Workflow, AgentLog, Document
from backend.app.schemas.agent import (
    AgentName,
    AgentOutput,
    AgentStatus,
)


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()



@pytest.fixture
def client(db_session):
    # Preserve dependency overrides configured by other test modules.
    previous_overrides = app.dependency_overrides.copy()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        # Restore the original overrides instead of clearing everything.
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)



@pytest.fixture
def valid_payload():
    return {
        "task": "Analyze authentication pull request",
        "source_type": "github_pull_request",
        "source_reference": "owner/repository/pull/10",
        "context": {
            "repository": "owner/repository",
            "commits": [
                {"message": "Add authentication feature"}
            ],
            "changed_files": [
                {
                    "filename": "backend/auth.py",
                    "patch": "+def authenticate():\n+    return True",
                }
            ],
        },
    }


def create_successful_results():
    return {
        "documentation": AgentOutput(
            agent_name=AgentName.DOCUMENTATION,
            status=AgentStatus.COMPLETED,
            result={
                "summary": "Documentation generated.",
                "generated_markdown": "# Authentication Update",
                "files_covered": ["README.md"],
                "documentation_gaps": [],
            },
        ),
        "code_review": AgentOutput(
            agent_name=AgentName.CODE_REVIEW,
            status=AgentStatus.COMPLETED,
            result={
                "summary": "Code review completed.",
                "findings": [],
                "overall_risk": "INFO",
                "recommendations": [],
            },
        ),
        "team_intelligence": AgentOutput(
            agent_name=AgentName.TEAM_INTELLIGENCE,
            status=AgentStatus.COMPLETED,
            result={
                "summary": "Team analysis completed.",
                "completed_items": [],
                "decisions": [],
                "action_items": [],
                "blockers": [],
            },
        ),
    }


def test_analyze_agents_success(
    client,
    db_session,
    monkeypatch,
    valid_payload,
):
    async def mock_run(agent_input):
        return create_successful_results()

    monkeypatch.setattr(agents.orchestrator, "run", mock_run)

    response = client.post(
        "/api/v1/agents/analyze",
        json=valid_payload,
    )

    assert response.status_code == 200

    # Verify workflow persistence.
    workflows = db_session.scalars(
        select(Workflow)
    ).all()

    assert len(workflows) == 1
    workflow = workflows[0]

    assert workflow.status == "COMPLETED"
    assert workflow.title == valid_payload["task"]

    # Verify agent logs.
    logs = db_session.scalars(
        select(AgentLog).where(
            AgentLog.workflow_id == workflow.id
        )
    ).all()

    assert len(logs) == 3

    # Verify generated document.
    documents = db_session.scalars(
        select(Document).where(
            Document.workflow_id == workflow.id
        )
    ).all()

    assert len(documents) == 1
    assert documents[0].content == "# Authentication Update"


def test_analyze_agents_invalid_payload(
    client,
    valid_payload,
):
    valid_payload.pop("task")

    response = client.post(
        "/api/v1/agents/analyze",
        json=valid_payload,
    )

    assert response.status_code == 422


def test_analyze_agents_all_failed(
    client,
    db_session,
    monkeypatch,
    valid_payload,
):
    failed_results = {
        "documentation": AgentOutput(
            agent_name=AgentName.DOCUMENTATION,
            status=AgentStatus.FAILED,
            error="Documentation failed.",
        ),
        "code_review": AgentOutput(
            agent_name=AgentName.CODE_REVIEW,
            status=AgentStatus.FAILED,
            error="Code review failed.",
        ),
        "team_intelligence": AgentOutput(
            agent_name=AgentName.TEAM_INTELLIGENCE,
            status=AgentStatus.FAILED,
            error="Team analysis failed.",
        ),
    }

    async def mock_run(agent_input):
        return failed_results

    monkeypatch.setattr(agents.orchestrator, "run", mock_run)

    response = client.post(
        "/api/v1/agents/analyze",
        json=valid_payload,
    )

    assert response.status_code == 500

    # Failure logs must still be saved.
    workflows = db_session.scalars(
        select(Workflow)
    ).all()

    assert len(workflows) == 1
    assert workflows[0].status == "FAILED"

    logs = db_session.scalars(
        select(AgentLog).where(
            AgentLog.workflow_id == workflows[0].id
        )
    ).all()

    assert len(logs) == 3


def test_analyze_agents_orchestration_error(
    client,
    db_session,
    monkeypatch,
    valid_payload,
):
    async def mock_run(agent_input):
        raise RuntimeError("Internal test error")

    monkeypatch.setattr(agents.orchestrator, "run", mock_run)

    response = client.post(
        "/api/v1/agents/analyze",
        json=valid_payload,
    )

    assert response.status_code == 500

    workflows = db_session.scalars(
        select(Workflow)
    ).all()

    assert len(workflows) == 0


def test_analyze_agents_nonexistent_workflow(
    client,
    valid_payload,
):
    valid_payload["workflow_id"] = 9999

    response = client.post(
        "/api/v1/agents/analyze",
        json=valid_payload,
    )

    assert response.status_code == 404