import asyncio

from backend.app.agents.documentation_agent import DocumentationAgent
from backend.app.agents.code_review_agent import CodeReviewAgent
from backend.app.agents.team_intelligence_agent import TeamIntelligenceAgent

from backend.app.schemas.agent import (
    AgentInput,
    AgentOutput,
    AgentStatus,
)


class AgentOrchestrator:
    """
    Coordinates all three DocuMind AI agents.

    Execution strategy:
    1. Documentation and Code Review run concurrently.
    2. Team Intelligence processes their results.
    3. All outputs are returned together.
    """

    def __init__(self):
        self.documentation_agent = DocumentationAgent()
        self.code_review_agent = CodeReviewAgent()
        self.team_intelligence_agent = TeamIntelligenceAgent()

    async def run(
        self,
        agent_input: AgentInput
    ) -> dict[str, AgentOutput]:

        context = agent_input.context

        # Extract repository information.
        repository = context.get(
            "repository",
            "Unknown repository"
        )

        commits = context.get(
            "commits",
            []
        )

        changed_files = context.get(
            "changed_files",
            []
        )

        # Validate changed files before execution.
        if not isinstance(changed_files, list):
            raise ValueError("changed_files must be a list.")

        # Prepare input for Documentation Agent.
        # Documentation Agent supports strings and dictionaries.
        documentation_input = agent_input.model_copy(
            update={
                "context": {
                    "repository": repository,
                    "commits": commits,
                    "changed_files": changed_files,
                }
            }
        )

        # Normalize changed files for Code Review Agent.
        # Code Review Agent expects dictionaries containing filename
        # and an optional patch.
        review_changed_files = []

        for item in changed_files:

            if isinstance(item, str):
                review_changed_files.append({
                    "filename": item,
                    "patch": ""
                })

            elif isinstance(item, dict):
                review_changed_files.append(item)

            else:
                raise ValueError(
                    "Each changed file must be a string or dictionary."
                )

        # Prepare input for Code Review Agent.
        review_input = agent_input.model_copy(
            update={
                "context": {
                    "changed_files": review_changed_files,
                }
            }
        )

        # Execute Documentation and Code Review agents concurrently.
        documentation_result, review_result = await asyncio.gather(
            self.documentation_agent.run(documentation_input),
            self.code_review_agent.run(review_input),
        )

        # Extract information for Team Intelligence Agent.

        # Preserve information supplied by the original request.
        completed_items = list(
            context.get("completed_items", [])
        )

        decisions = list(
            context.get("decisions", [])
        )

        blockers = list(
            context.get("blockers", [])
        )

        action_items = list(
            context.get("action_items", [])
        )

        # Add results from Documentation and Code Review agents.
        for name, result in [
            ("Documentation Agent", documentation_result),
            ("Code Review Agent", review_result),
        ]:

            if result.status == AgentStatus.COMPLETED:
                completed_items.append(
                    f"{name} completed successfully."
                )

            else:
                blockers.append(
                    f"{name} execution failed."
                )

        # Add repository context without discarding existing decisions.
        if repository != "Unknown repository":

            repository_decision = (
                f"Repository analyzed: {repository}"
            )

            if repository_decision not in decisions:
                decisions.append(repository_decision)

        # Prepare Team Intelligence input.
        team_context = {
            "completed_items": completed_items,
            "decisions": decisions,
            "blockers": blockers,
            "action_items": action_items,

            "documentation_result": (
                documentation_result.result
                if documentation_result.status == AgentStatus.COMPLETED
                else None
            ),

            "code_review_result": (
                review_result.result
                if review_result.status == AgentStatus.COMPLETED
                else None
            ),
        }

        team_input = agent_input.model_copy(
            update={
                "context": team_context
            }
        )

        # Execute Team Intelligence Agent.
        team_result = await self.team_intelligence_agent.run(
            team_input
        )

        # Return all agent outputs.
        return {
            "documentation": documentation_result,
            "code_review": review_result,
            "team_intelligence": team_result,
        }