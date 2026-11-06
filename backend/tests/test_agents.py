import pytest
from backend.app.agents.team_intelligence_agent import TeamIntelligenceAgent
from backend.app.agents.documentation_agent import DocumentationAgent
from backend.app.schemas.agent import (
    AgentInput,
    AgentName,
    AgentStatus,
)


@pytest.mark.anyio
async def test_documentation_agent_success():

    agent = DocumentationAgent()

    agent_input = AgentInput(
        task="Document recent API changes",
        source_type="github_commits",
        context={
            "repository": "owner/project",
            "commits": [
                {"message": "Add authentication API"},
                {"message": "Add JWT validation"},
            ],
            "changed_files": [
                "backend/app/routes/auth.py",
                "backend/app/services/auth_service.py",
            ],
        },
    )

    output = await agent.run(agent_input)

    assert output.agent_name == AgentName.DOCUMENTATION
    assert output.status == AgentStatus.COMPLETED

    assert output.result["summary"]
    assert "# Technical Change Documentation" in (
        output.result["generated_markdown"]
    )

    assert len(output.result["files_covered"]) == 2
    assert output.execution_time_ms >= 0


@pytest.mark.anyio
async def test_documentation_agent_empty_context():

    agent = DocumentationAgent()

    agent_input = AgentInput(
        task="Generate documentation",
        context={}
    )

    output = await agent.run(agent_input)

    assert output.agent_name == AgentName.DOCUMENTATION
    assert output.status == AgentStatus.FAILED
    assert output.error == "Agent execution failed."


@pytest.mark.anyio
async def test_documentation_agent_invalid_commits():

    agent = DocumentationAgent()

    agent_input = AgentInput(
        task="Generate documentation",
        context={
            "commits": "not-a-list"
        }
    )

    output = await agent.run(agent_input)

    assert output.status == AgentStatus.FAILED

from backend.app.agents.code_review_agent import CodeReviewAgent


@pytest.mark.anyio
async def test_code_review_agent_detects_security_issues():

    agent = CodeReviewAgent()

    agent_input = AgentInput(
        task="Review pull request changes",
        source_type="github_pull_request",
        context={
            "changed_files": [
                {
                    "filename": "backend/app/config.py",
                    "patch": """
+api_key = "supersecretcredential123"
+eval(user_input)
+requests.get(url, verify=False)
"""
                }
            ]
        }
    )

    output = await agent.run(agent_input)

    assert output.agent_name == AgentName.CODE_REVIEW
    assert output.status == AgentStatus.COMPLETED

    findings = output.result["findings"]

    assert len(findings) == 3

    titles = [
        finding["title"]
        for finding in findings
    ]

    assert "Potential hardcoded credential" in titles
    assert "Potential unsafe eval() usage" in titles
    assert "TLS certificate verification disabled" in titles

    assert output.result["overall_risk"] == "HIGH"


@pytest.mark.anyio
async def test_code_review_agent_clean_code():

    agent = CodeReviewAgent()

    agent_input = AgentInput(
        task="Review clean code",
        context={
            "changed_files": [
                {
                    "filename": "backend/app/main.py",
                    "patch": """
+def calculate_total(price, quantity):
+    return price * quantity
"""
                }
            ]
        }
    )

    output = await agent.run(agent_input)

    assert output.status == AgentStatus.COMPLETED
    assert output.result["findings"] == []
    assert output.result["overall_risk"] == "INFO"


@pytest.mark.anyio
async def test_code_review_agent_invalid_input():

    agent = CodeReviewAgent()

    agent_input = AgentInput(
        task="Review invalid input",
        context={
            "changed_files": "invalid data"
        }
    )

    output = await agent.run(agent_input)

    assert output.status == AgentStatus.FAILED
    assert output.error == "Agent execution failed."


@pytest.mark.anyio
async def test_code_review_agent_invalid_file_structure():

    agent = CodeReviewAgent()

    agent_input = AgentInput(
        task="Review invalid file structure",
        context={
            "changed_files": [
                "this should be a dictionary"
            ]
        }
    )

    output = await agent.run(agent_input)

    assert output.status == AgentStatus.FAILED


@pytest.mark.anyio
async def test_team_intelligence_agent_success():

    agent = TeamIntelligenceAgent()

    agent_input = AgentInput(
        task="Generate team progress report",
        source_type="team_update",
        context={
            "completed_items": [
                "Implemented GitHub authentication",
                "Added PR review API",
                "Fixed pagination bug",
            ],
            "decisions": [
                "Use FastAPI for backend",
                "Use SQLite for initial storage",
            ],
            "blockers": [
                "GitHub API rate limit issue",
            ],
            "action_items": [
                {
                    "title": "Write integration tests",
                    "description": "Cover all GitHub endpoints",
                    "owner": "Backend Developer",
                    "priority": "HIGH",
                },
                {
                    "title": "Complete API documentation",
                    "priority": "MEDIUM",
                },
            ],
        },
    )

    output = await agent.run(agent_input)

    assert output.agent_name == AgentName.TEAM_INTELLIGENCE
    assert output.status == AgentStatus.COMPLETED

    assert len(output.result["completed_items"]) == 3
    assert len(output.result["decisions"]) == 2
    assert len(output.result["blockers"]) == 1
    assert len(output.result["action_items"]) == 2

    assert "3 completed items" in output.result["summary"]


@pytest.mark.anyio
async def test_team_intelligence_agent_empty_context():

    agent = TeamIntelligenceAgent()

    agent_input = AgentInput(
        task="Generate an empty team report",
        context={},
    )

    output = await agent.run(agent_input)

    assert output.status == AgentStatus.COMPLETED

    assert output.result["completed_items"] == []
    assert output.result["decisions"] == []
    assert output.result["blockers"] == []
    assert output.result["action_items"] == []


@pytest.mark.anyio
async def test_team_intelligence_agent_invalid_input():

    agent = TeamIntelligenceAgent()

    agent_input = AgentInput(
        task="Test invalid team input",
        context={
            "completed_items": "not-a-list",
        },
    )

    output = await agent.run(agent_input)

    assert output.status == AgentStatus.FAILED
    assert output.error == "Agent execution failed."


@pytest.mark.anyio
async def test_team_intelligence_agent_invalid_action_item():

    agent = TeamIntelligenceAgent()

    agent_input = AgentInput(
        task="Test invalid action item",
        context={
            "action_items": [
                {
                    "title": "",
                    "priority": "URGENT",
                }
            ],
        },
    )

    output = await agent.run(agent_input)

    assert output.status == AgentStatus.FAILED
    assert output.error == "Agent execution failed."