import pytest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database.base import Base
from backend.app.models import Workflow, AgentLog, Document
from backend.app.schemas.agent import (
    AgentInput,
    AgentName,
    AgentOutput,
    AgentStatus,
)
from backend.app.services.agent_persistence_service import (
    persist_agent_results,
)


# Use a separate in-memory SQLite database for testing.
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
def agent_input():
    return AgentInput(
        task="Analyze authentication pull request",
        source_type="github_pull_request",
        source_reference="owner/repository/pull/10",
        context={},
    )


@pytest.fixture
def successful_results():
    return {
        "documentation": AgentOutput(
            agent_name=AgentName.DOCUMENTATION,
            status=AgentStatus.COMPLETED,
            result={
                "summary": "Documentation generated",
                "generated_markdown": "# Authentication Update\n\nDocumentation content.",
                "files_covered": ["README.md"],
                "documentation_gaps": [],
            },
            execution_time_ms=100,
        ),
        "code_review": AgentOutput(
            agent_name=AgentName.CODE_REVIEW,
            status=AgentStatus.COMPLETED,
            result={
                "summary": "Code review completed",
                "findings": [],
                "overall_risk": "INFO",
                "recommendations": [],
            },
            execution_time_ms=150,
        ),
        "team_intelligence": AgentOutput(
            agent_name=AgentName.TEAM_INTELLIGENCE,
            status=AgentStatus.COMPLETED,
            result={
                "summary": "Team analysis completed",
                "completed_items": ["Authentication reviewed"],
                "decisions": [],
                "action_items": [],
                "blockers": [],
            },
            execution_time_ms=80,
        ),
    }


def test_persist_successful_agent_results(
    db_session,
    agent_input,
    successful_results,
):
    workflow = persist_agent_results(
        db_session,
        agent_input,
        successful_results,
    )

    assert workflow.id is not None
    assert workflow.status == "COMPLETED"

    logs = db_session.scalars(
        select(AgentLog).where(
            AgentLog.workflow_id == workflow.id
        )
    ).all()

    assert len(logs) == 3

    documents = db_session.scalars(
        select(Document).where(
            Document.workflow_id == workflow.id
        )
    ).all()

    assert len(documents) == 1
    assert documents[0].document_type == "MARKDOWN"
    assert "# Authentication Update" in documents[0].content


def test_persist_partial_agent_failure(
    db_session,
    agent_input,
    successful_results,
):
    successful_results["code_review"] = AgentOutput(
        agent_name=AgentName.CODE_REVIEW,
        status=AgentStatus.FAILED,
        error="Code review failed.",
    )

    workflow = persist_agent_results(
        db_session,
        agent_input,
        successful_results,
    )

    assert workflow.status == "PARTIAL"

    logs = db_session.scalars(
        select(AgentLog).where(
            AgentLog.workflow_id == workflow.id
        )
    ).all()

    assert len(logs) == 3


def test_persist_all_agents_failed(
    db_session,
    agent_input,
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

    workflow = persist_agent_results(
        db_session,
        agent_input,
        failed_results,
    )

    assert workflow.status == "FAILED"

    logs = db_session.scalars(
        select(AgentLog).where(
            AgentLog.workflow_id == workflow.id
        )
    ).all()

    assert len(logs) == 3


def test_persist_results_to_existing_workflow(
    db_session,
    successful_results,
):
    existing_workflow = Workflow(
        title="Existing PR analysis",
        description="Previously created workflow",
        status="PENDING",
    )

    db_session.add(existing_workflow)
    db_session.commit()
    db_session.refresh(existing_workflow)

    agent_input = AgentInput(
        workflow_id=existing_workflow.id,
        task="Analyze existing workflow",
        context={},
    )

    workflow = persist_agent_results(
        db_session,
        agent_input,
        successful_results,
    )

    assert workflow.id == existing_workflow.id
    assert workflow.status == "COMPLETED"


def test_persist_invalid_workflow_id_rolls_back(
    db_session,
    successful_results,
):
    agent_input = AgentInput(
        workflow_id=9999,
        task="Analyze missing workflow",
        context={},
    )

    with pytest.raises(ValueError, match="not found"):
        persist_agent_results(
            db_session,
            agent_input,
            successful_results,
        )

    workflows = db_session.scalars(
        select(Workflow)
    ).all()

    assert len(workflows) == 0