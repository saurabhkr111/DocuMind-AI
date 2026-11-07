from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session, selectinload

from backend.app.auth import Principal, get_current_principal
from backend.app.database.connection import get_db
from backend.app.models import Workflow

from backend.app.schemas.workflow import (
    WorkflowCreate,
    WorkflowResponse,
    WorkflowUpdate,
    WorkflowDetailResponse,
)


router = APIRouter(
    prefix="/api/v1/workflows",
    tags=["Workflows"]
)


# -----------------------------------------
# CREATE WORKFLOW
# -----------------------------------------

@router.post(
    "/",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED
)
def create_workflow(
    workflow_data: WorkflowCreate,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    try:
        new_workflow = Workflow(
            title=workflow_data.title,
            description=workflow_data.description,
            source_type=workflow_data.source_type,
            source_reference=workflow_data.source_reference,
            status="PENDING"
        )

        db.add(new_workflow)
        db.commit()
        db.refresh(new_workflow)

        return new_workflow

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create workflow."
        )


# -----------------------------------------
# GET ALL WORKFLOWS
# -----------------------------------------

@router.get(
    "/",
    response_model=list[WorkflowResponse]
)
def get_all_workflows(
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    return (
        db.query(Workflow)
        .order_by(Workflow.id.desc())
        .all()
    )


# -----------------------------------------
# GET COMPLETE WORKFLOW HISTORY
# -----------------------------------------

@router.get(
    "/{workflow_id}/details",
    response_model=WorkflowDetailResponse
)
def get_workflow_details(
    workflow_id: int,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    workflow = (
        db.query(Workflow)
        .options(
            selectinload(Workflow.agent_logs),
            selectinload(Workflow.documents)
        )
        .filter(Workflow.id == workflow_id)
        .first()
    )

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found."
        )

    return workflow


# -----------------------------------------
# GET WORKFLOW BY ID
# -----------------------------------------

@router.get(
    "/{workflow_id}",
    response_model=WorkflowResponse
)
def get_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    workflow = (
        db.query(Workflow)
        .filter(Workflow.id == workflow_id)
        .first()
    )

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found."
        )

    return workflow


# -----------------------------------------
# UPDATE WORKFLOW
# -----------------------------------------

@router.put(
    "/{workflow_id}",
    response_model=WorkflowResponse
)
def update_workflow(
    workflow_id: int,
    workflow_data: WorkflowUpdate,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    workflow = (
        db.query(Workflow)
        .filter(Workflow.id == workflow_id)
        .first()
    )

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found."
        )

    update_data = workflow_data.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():
        setattr(workflow, key, value)

    db.commit()
    db.refresh(workflow)

    return workflow


# -----------------------------------------
# DELETE WORKFLOW
# -----------------------------------------

@router.delete(
    "/{workflow_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    workflow = (
        db.query(Workflow)
        .filter(Workflow.id == workflow_id)
        .first()
    )

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found."
        )

    db.delete(workflow)
    db.commit()

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )
