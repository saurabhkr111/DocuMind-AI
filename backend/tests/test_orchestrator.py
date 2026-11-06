import pytest

from backend.app.orchestrator import agent_orchestrator
from backend.app.schemas.agent import (
    AgentInput,
    AgentName,
    AgentOutput,
    AgentStatus,
)


def create_agent_output(agent_name, status=AgentStatus.COMPLETED):
    """Create a sample agent output for testing."""

    return AgentOutput(
        agent_name=agent_name,
        status=status,
        result={"summary": "Test completed successfully."}
        if status == AgentStatus.COMPLETED
        else None,
        error="Test agent failure."
        if status == AgentStatus.FAILED
        else None,
        execution_time_ms=10.0,
    )


@pytest.fixture
def sample_input():
    """Provide sample GitHub pull request data."""

    return AgentInput(
        workflow_id=1,
        task="Analyze this GitHub pull request.",
        source_type="github_pull_request",
        source_reference="owner/repository/pull/10",
        context={
            "repository": "owner/repository",
            "commits": [
                {"message": "Add authentication feature"}
            ],
            "changed_files": [
                {
                    "filename": "backend/auth.py",
                    "patch": "+ def authenticate(): pass"
                },
                {
                    "filename": "README.md",
                    "patch": "+ Added authentication documentation"
                },
            ],
        },
    )


@pytest.mark.anyio
async def test_orchestrator_handles_agent_failure(
    monkeypatch,
    sample_input
):
    """Verify that one failed agent does not stop orchestration."""

    captured_team_input = {}

    class FakeDocumentationAgent:
        async def run(self, agent_input):
            return create_agent_output(
                AgentName.DOCUMENTATION,
                AgentStatus.FAILED,
            )

    class FakeCodeReviewAgent:
        async def run(self, agent_input):
            return create_agent_output(
                AgentName.CODE_REVIEW
            )

    class FakeTeamIntelligenceAgent:
        async def run(self, agent_input):
            captured_team_input.update(agent_input.context)

            return create_agent_output(
                AgentName.TEAM_INTELLIGENCE
            )

    monkeypatch.setattr(
        agent_orchestrator,
        "DocumentationAgent",
        FakeDocumentationAgent,
    )

    monkeypatch.setattr(
        agent_orchestrator,
        "CodeReviewAgent",
        FakeCodeReviewAgent,
    )

    monkeypatch.setattr(
        agent_orchestrator,
        "TeamIntelligenceAgent",
        FakeTeamIntelligenceAgent,
    )

    orchestrator = agent_orchestrator.AgentOrchestrator()

    results = await orchestrator.run(sample_input)

    assert results["documentation"].status == AgentStatus.FAILED

    assert results["code_review"].status == AgentStatus.COMPLETED

    assert results["team_intelligence"].status == AgentStatus.COMPLETED

    # Failed agent must appear as a blocker.
    assert (
        "Documentation Agent execution failed."
        in captured_team_input["blockers"]
    )

    # Only successful agents should appear as completed.
    assert (
        "Code Review Agent completed successfully."
        in captured_team_input["completed_items"]
    )

    assert not any(
        "Documentation Agent completed successfully."
        in item
        for item in captured_team_input["completed_items"]
    )


@pytest.mark.anyio
async def test_orchestrator_success(monkeypatch, sample_input):
    """Verify that all three agents complete successfully."""

    class FakeDocumentationAgent:
        async def run(self, agent_input):
            return create_agent_output(AgentName.DOCUMENTATION)

    class FakeCodeReviewAgent:
        async def run(self, agent_input):
            return create_agent_output(AgentName.CODE_REVIEW)

    class FakeTeamIntelligenceAgent:
        async def run(self, agent_input):
            return create_agent_output(AgentName.TEAM_INTELLIGENCE)

    monkeypatch.setattr(
        agent_orchestrator,
        "DocumentationAgent",
        FakeDocumentationAgent,
    )

    monkeypatch.setattr(
        agent_orchestrator,
        "CodeReviewAgent",
        FakeCodeReviewAgent,
    )

    monkeypatch.setattr(
        agent_orchestrator,
        "TeamIntelligenceAgent",
        FakeTeamIntelligenceAgent,
    )

    orchestrator = agent_orchestrator.AgentOrchestrator()

    results = await orchestrator.run(sample_input)

    assert results["documentation"].status == AgentStatus.COMPLETED
    assert results["code_review"].status == AgentStatus.COMPLETED
    assert results["team_intelligence"].status == AgentStatus.COMPLETED



@pytest.mark.anyio
async def test_documentation_agent_receives_filenames(
    monkeypatch,
    sample_input
):
    """Verify that documentation receives filenames as strings."""

    captured_input = {}

    class FakeDocumentationAgent:
        async def run(self, agent_input):
            captured_input.update(agent_input.context)

            return create_agent_output(AgentName.DOCUMENTATION)

    class FakeCodeReviewAgent:
        async def run(self, agent_input):
            return create_agent_output(AgentName.CODE_REVIEW)

    class FakeTeamIntelligenceAgent:
        async def run(self, agent_input):
            return create_agent_output(AgentName.TEAM_INTELLIGENCE)

    monkeypatch.setattr(
        agent_orchestrator,
        "DocumentationAgent",
        FakeDocumentationAgent,
    )

    monkeypatch.setattr(
        agent_orchestrator,
        "CodeReviewAgent",
        FakeCodeReviewAgent,
    )

    monkeypatch.setattr(
        agent_orchestrator,
        "TeamIntelligenceAgent",
        FakeTeamIntelligenceAgent,
    )

    orchestrator = agent_orchestrator.AgentOrchestrator()

    await orchestrator.run(sample_input)

    assert captured_input["changed_files"] == [
        "backend/auth.py",
        "README.md",
    ]


@pytest.mark.anyio
async def test_code_review_agent_receives_file_patches(
    monkeypatch,
    sample_input
):
    """Verify that code review receives the original patch information."""

    captured_input = {}

    class FakeDocumentationAgent:
        async def run(self, agent_input):
            return create_agent_output(AgentName.DOCUMENTATION)

    class FakeCodeReviewAgent:
        async def run(self, agent_input):
            captured_input.update(agent_input.context)

            return create_agent_output(AgentName.CODE_REVIEW)

    class FakeTeamIntelligenceAgent:
        async def run(self, agent_input):
            return create_agent_output(AgentName.TEAM_INTELLIGENCE)

    monkeypatch.setattr(
        agent_orchestrator,
        "DocumentationAgent",
        FakeDocumentationAgent,
    )

    monkeypatch.setattr(
        agent_orchestrator,
        "CodeReviewAgent",
        FakeCodeReviewAgent,
    )

    monkeypatch.setattr(
        agent_orchestrator,
        "TeamIntelligenceAgent",
        FakeTeamIntelligenceAgent,
    )

    orchestrator = agent_orchestrator.AgentOrchestrator()

    await orchestrator.run(sample_input)

    assert captured_input["changed_files"] == (
        sample_input.context["changed_files"]
    )

    assert "patch" in captured_input["changed_files"][0]


@pytest.mark.anyio
async def test_team_intelligence_receives_agent_results(
    monkeypatch,
    sample_input
):
    """Verify that team intelligence receives completion information."""

    captured_input = {}

    class FakeDocumentationAgent:
        async def run(self, agent_input):
            return create_agent_output(AgentName.DOCUMENTATION)

    class FakeCodeReviewAgent:
        async def run(self, agent_input):
            return create_agent_output(AgentName.CODE_REVIEW)

    class FakeTeamIntelligenceAgent:
        async def run(self, agent_input):
            captured_input.update(agent_input.context)

            return create_agent_output(AgentName.TEAM_INTELLIGENCE)

    monkeypatch.setattr(
        agent_orchestrator,
        "DocumentationAgent",
        FakeDocumentationAgent,
    )

    monkeypatch.setattr(
        agent_orchestrator,
        "CodeReviewAgent",
        FakeCodeReviewAgent,
    )

    monkeypatch.setattr(
        agent_orchestrator,
        "TeamIntelligenceAgent",
        FakeTeamIntelligenceAgent,
    )

    orchestrator = agent_orchestrator.AgentOrchestrator()

    await orchestrator.run(sample_input)

    assert len(captured_input["completed_items"]) == 2

    assert captured_input["blockers"] == []

    assert captured_input["decisions"] == [
        "Repository analyzed: owner/repository"
    ]



@pytest.mark.anyio
async def test_team_intelligence_preserves_original_context(
    monkeypatch,
    sample_input
):
    """Verify original team information reaches Team Intelligence."""

    original_action_items = [
        {
            "title": "Write authentication unit tests",
            "description": "Cover successful and failed login scenarios.",
            "owner": "Backend Developer",
            "priority": "HIGH",
        }
    ]

    original_decisions = [
        "Use JWT authentication."
    ]

    original_blockers = [
        "Waiting for API credentials."
    ]

    original_completed_items = [
        "Authentication endpoint implemented."
    ]

    sample_input = sample_input.model_copy(
        update={
            "context": {
                **sample_input.context,
                "action_items": original_action_items,
                "decisions": original_decisions,
                "blockers": original_blockers,
                "completed_items": original_completed_items,
            }
        }
    )

    captured_input = {}

    class FakeDocumentationAgent:
        async def run(self, agent_input):
            return create_agent_output(
                AgentName.DOCUMENTATION
            )

    class FakeCodeReviewAgent:
        async def run(self, agent_input):
            return create_agent_output(
                AgentName.CODE_REVIEW
            )

    class FakeTeamIntelligenceAgent:
        async def run(self, agent_input):
            captured_input.update(agent_input.context)

            return create_agent_output(
                AgentName.TEAM_INTELLIGENCE
            )

    monkeypatch.setattr(
        agent_orchestrator,
        "DocumentationAgent",
        FakeDocumentationAgent,
    )

    monkeypatch.setattr(
        agent_orchestrator,
        "CodeReviewAgent",
        FakeCodeReviewAgent,
    )

    monkeypatch.setattr(
        agent_orchestrator,
        "TeamIntelligenceAgent",
        FakeTeamIntelligenceAgent,
    )

    orchestrator = agent_orchestrator.AgentOrchestrator()

    await orchestrator.run(sample_input)

    # Original team information must be preserved.
    assert captured_input["action_items"] == original_action_items

    assert original_decisions[0] in captured_input["decisions"]

    assert original_blockers[0] in captured_input["blockers"]

    assert (
        original_completed_items[0]
        in captured_input["completed_items"]
    )

    # Results from both agents must also reach Team Intelligence.
    assert captured_input["documentation_result"] is not None

    assert captured_input["code_review_result"] is not None

    # The failed agent must appear as a blocker, not a completed item.
    # Only the successful Code Review Agent should be listed as completed.
    # The team agent receives this information through its input.