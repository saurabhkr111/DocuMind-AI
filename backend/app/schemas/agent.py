from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# --------------------------------------------------
# ENUMS
# --------------------------------------------------

class AgentName(str, Enum):
    DOCUMENTATION = "documentation"
    CODE_REVIEW = "code_review"
    TEAM_INTELLIGENCE = "team_intelligence"


class AgentStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class FindingSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# --------------------------------------------------
# COMMON AGENT INPUT
# --------------------------------------------------

class AgentInput(BaseModel):
    """Standard input accepted by an AI agent."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: int | None = Field(default=None, ge=1)

    task: str = Field(
        ...,
        min_length=1,
        max_length=5000
    )

    source_type: Literal[
        "github_repository",
        "github_pull_request",
        "github_commits",
        "team_update",
        "manual"
    ] | None = None

    source_reference: str | None = None

    context: dict[str, Any] = Field(default_factory=dict)


# --------------------------------------------------
# COMMON AGENT OUTPUT
# --------------------------------------------------

class AgentOutput(BaseModel):
    """Standard response returned by an AI agent."""

    model_config = ConfigDict(extra="forbid")

    agent_name: AgentName

    status: AgentStatus

    result: dict[str, Any] | None = None

    error: str | None = None

    execution_time_ms: float | None = Field(
        default=None,
        ge=0
    )


# --------------------------------------------------
# CODE REVIEW RESULT
# --------------------------------------------------

class AgentFinding(BaseModel):
    """Represents an issue or observation found during review."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)

    description: str

    severity: FindingSeverity

    category: str | None = None

    file_path: str | None = None

    line_number: int | None = Field(
        default=None,
        ge=1
    )

    recommendation: str | None = None


class CodeReviewResult(BaseModel):
    """Structured output from the Code Review Agent."""

    summary: str

    findings: list[AgentFinding] = Field(default_factory=list)

    overall_risk: FindingSeverity = FindingSeverity.INFO

    recommendations: list[str] = Field(default_factory=list)


# --------------------------------------------------
# DOCUMENTATION RESULT
# --------------------------------------------------

class DocumentationResult(BaseModel):
    """Structured output from the Documentation Agent."""

    summary: str

    generated_markdown: str

    files_covered: list[str] = Field(default_factory=list)

    documentation_gaps: list[str] = Field(default_factory=list)


# --------------------------------------------------
# TEAM INTELLIGENCE RESULT
# --------------------------------------------------

class TeamActionItem(BaseModel):
    """Represents an action identified from team activity."""

    title: str = Field(min_length=1)

    description: str | None = None

    owner: str | None = None

    priority: Literal[
        "LOW",
        "MEDIUM",
        "HIGH"
    ] = "MEDIUM"


class TeamIntelligenceResult(BaseModel):
    """Structured output from the Team Intelligence Agent."""

    summary: str

    completed_items: list[str] = Field(default_factory=list)

    decisions: list[str] = Field(default_factory=list)

    action_items: list[TeamActionItem] = Field(default_factory=list)

    blockers: list[str] = Field(default_factory=list)