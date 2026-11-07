from abc import ABC, abstractmethod
from time import perf_counter
from typing import Any

from pydantic import BaseModel

from backend.app.schemas.agent import (
    AgentInput,
    AgentOutput,
    AgentName,
    AgentStatus,
)


class BaseAgent(ABC):
    """
    Common base class for all DocuMind AI agents.

    Every specialized agent must implement its own execute()
    method and return a Pydantic result model.
    """

    agent_name: AgentName

    @abstractmethod
    async def execute(self, agent_input: AgentInput) -> BaseModel:
        """
        Execute the agent's specialized task.

        Subclasses must implement this method.
        """
        raise NotImplementedError

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        """
        Common execution wrapper.

        Handles execution time, successful responses,
        and failures consistently.
        """

        start_time = perf_counter()

        try:
            result = await self.execute(agent_input)

            if not isinstance(result, BaseModel):
                raise TypeError(
                    "Agent execute() must return a Pydantic model."
                )

            execution_time = (
                perf_counter() - start_time
            ) * 1000

            return AgentOutput(
                agent_name=self.agent_name,
                status=AgentStatus.COMPLETED,
                result=result.model_dump(mode="json"),
                execution_time_ms=round(execution_time, 2),
            )
        except Exception:
            execution_time = (
                perf_counter() - start_time
                ) * 1000
            return AgentOutput(
        agent_name=self.agent_name,
        status=AgentStatus.FAILED,
        error="Agent execution failed.",
        execution_time_ms=round(execution_time, 2),
    )
        