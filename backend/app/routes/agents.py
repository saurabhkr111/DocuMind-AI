from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.models import Workflow
from backend.app.orchestrator.agent_orchestrator import AgentOrchestrator
from backend.app.schemas.agent import (
    AgentInput,
    AgentOutput,
    AgentStatus,
)
from backend.app.services.agent_persistence_service import (
    persist_agent_results,
)


router = APIRouter(
    prefix="/api/v1/agents",
    tags=["AI Agents"],
)

orchestrator = AgentOrchestrator()


@router.post(
    "/analyze",
    response_model=dict[str, AgentOutput],
    status_code=status.HTTP_200_OK,
)
async def analyze_with_agents(
    agent_input: AgentInput,
    db: Session = Depends(get_db),
):
    """
    Execute all three agents and persist their results.

    Saves:
    - Workflow information
    - Agent execution logs
    - Generated documentation
    """

    try:
        # 1. Validate an existing workflow ID.
        if agent_input.workflow_id is not None:

            workflow = db.get(
                Workflow,
                agent_input.workflow_id,
            )

            if workflow is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Workflow not found.",
                )

        # 2. Execute all three agents.
        results = await orchestrator.run(agent_input)

        # 3. Persist workflow, agent logs and documents.
        workflow = persist_agent_results(
            db=db,
            agent_input=agent_input,
            results=results,
        )

        # 4. Check whether all agents failed.
        if not results or all(
            result.status == AgentStatus.FAILED
            for result in results.values()
        ):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="All agents failed to execute.",
            )

        # 5. Return agent results.
        return results

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        )

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent orchestration or persistence failed.",
        )

