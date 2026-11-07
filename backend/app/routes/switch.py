from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.auth import Principal, get_current_principal
from backend.app.database.connection import get_db
from backend.app.routes.agents import analyze_with_agents
from backend.app.schemas.agent import AgentInput, AgentOutput


router = APIRouter(
    prefix="/api/v1/switch",
    tags=["Switch Integration"],
)


@router.post(
    "/webhook",
    response_model=dict[str, AgentOutput],
    status_code=status.HTTP_200_OK,
)
async def switch_webhook(
    agent_input: AgentInput,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    """
    Receive authenticated task events from Switch.

    Reuses the existing DocuMind agent orchestration
    and persistence implementation.
    """
    return await analyze_with_agents(
        agent_input=agent_input,
        db=db,
        principal=principal,
    )
