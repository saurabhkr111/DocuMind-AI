from pydantic import BaseModel

from backend.app.agents.base_agent import BaseAgent
from backend.app.schemas.agent import (
    AgentInput,
    AgentName,
    TeamIntelligenceResult,
    TeamActionItem,
)


class TeamIntelligenceAgent(BaseAgent):
    """
    Converts team updates into structured intelligence reports.

    Initial implementation uses deterministic processing.
    LLM integration will be introduced later.
    """

    agent_name = AgentName.TEAM_INTELLIGENCE

    async def execute(
        self,
        agent_input: AgentInput
    ) -> BaseModel:

        context = agent_input.context

        completed_items = context.get(
            "completed_items", []
        )

        decisions = context.get(
            "decisions", []
        )

        blockers = context.get(
            "blockers", []
        )

        action_items_data = context.get(
            "action_items", []
        )

        if not isinstance(completed_items, list):
            raise ValueError("completed_items must be a list.")

        if not isinstance(decisions, list):
            raise ValueError("decisions must be a list.")

        if not isinstance(blockers, list):
            raise ValueError("blockers must be a list.")

        if not isinstance(action_items_data, list):
            raise ValueError("action_items must be a list.")

        # Validate textual lists.
        for item in completed_items + decisions + blockers:
            if not isinstance(item, str):
                raise ValueError(
                    "Team update entries must be strings."
                )

        # Convert action item dictionaries into Pydantic models.
        action_items = [
            TeamActionItem(**item)
            for item in action_items_data
            if isinstance(item, dict)
        ]

        if len(action_items) != len(action_items_data):
            raise ValueError(
                "Each action item must be an object."
            )

        summary = self._generate_summary(
            completed_items,
            decisions,
            blockers,
            action_items
        )

        return TeamIntelligenceResult(
            summary=summary,
            completed_items=completed_items,
            decisions=decisions,
            action_items=action_items,
            blockers=blockers,
        )

    @staticmethod
    def _generate_summary(
        completed_items,
        decisions,
        blockers,
        action_items
    ):

        return (
            f"Team update: {len(completed_items)} completed items, "
            f"{len(decisions)} decisions, "
            f"{len(action_items)} pending action items, "
            f"and {len(blockers)} blockers."
        )