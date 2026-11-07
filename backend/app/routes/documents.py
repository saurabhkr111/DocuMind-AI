from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy import update
from sqlalchemy.orm import Session

from backend.app.auth import Principal, get_current_principal
from backend.app.database.connection import get_db
from backend.app.models import Document
from backend.app.schemas.document import (
    DocumentResponse,
    DocumentApprovalRequest,
    DocumentRejectionRequest,
)


router = APIRouter(
    prefix="/api/v1/documents",
    tags=["Documents"]
)


# -----------------------------------------
# HELPER: UPDATE WORKFLOW STATUS
# -----------------------------------------

def update_workflow_approval_status(
    db: Session,
    workflow_id: int
):
    documents = (
        db.query(Document)
        .filter(Document.workflow_id == workflow_id)
        .all()
    )

    # A workflow with an existing document should have
    # at least one document in this query.
    if not documents:
        return

    workflow = documents[0].workflow

    # Preserve agent execution failure states.
    # Document approval must not override these statuses.
    if workflow.status in {"PARTIAL", "FAILED"}:
        return

    approval_statuses = [
        document.approval_status
        for document in documents
    ]

    if "PENDING" in approval_statuses:
        workflow.status = "AWAITING_APPROVAL"

    elif "REJECTED" in approval_statuses:
        workflow.status = "REJECTED"

    elif approval_statuses and all(
        item == "APPROVED"
        for item in approval_statuses
    ):
        workflow.status = "APPROVED"


# -----------------------------------------
# GET DOCUMENT BY ID
# -----------------------------------------

@router.get(
    "/{document_id}",
    response_model=DocumentResponse
)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )

    return document


# -----------------------------------------
# APPROVE DOCUMENT
# -----------------------------------------

@router.post(
    "/{document_id}/approve",
    response_model=DocumentResponse
)
def approve_document(
    document_id: int,
    approval_data: DocumentApprovalRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    try:
        # Atomically approve only if the document is still PENDING.
        # reviewed_by always comes from the authenticated principal.
        result = db.execute(
            update(Document)
            .where(
                Document.id == document_id,
                Document.approval_status == "PENDING"
            )
            .values(
                approval_status="APPROVED",
                reviewed_by=principal.name,
                reviewed_at=datetime.now(timezone.utc),
                approval_reason=None
            )
            .execution_options(synchronize_session=False)
        )

        # No row was updated: distinguish 404 from 409.
        if result.rowcount == 0:
            document = (
                db.query(Document)
                .filter(Document.id == document_id)
                .first()
            )

            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found."
                )

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Document has already been reviewed."
            )

        # Fetch the updated document.
        document = (
            db.query(Document)
            .filter(Document.id == document_id)
            .first()
        )

        # Update the associated workflow status.
        update_workflow_approval_status(
            db,
            document.workflow_id
        )

        db.commit()
        db.refresh(document)

        return document

    except Exception:
        db.rollback()
        raise


# -----------------------------------------
# REJECT DOCUMENT
# -----------------------------------------
@router.post(
    "/{document_id}/reject",
    response_model=DocumentResponse
)
def reject_document(
    document_id: int,
    rejection_data: DocumentRejectionRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    try:
        # Atomically reject only if the document is still PENDING.
        # reviewed_by always comes from the authenticated principal.
        result = db.execute(
            update(Document)
            .where(
                Document.id == document_id,
                Document.approval_status == "PENDING"
            )
            .values(
                approval_status="REJECTED",
                reviewed_by=principal.name,
                reviewed_at=datetime.now(timezone.utc),
                approval_reason=rejection_data.reason
            )
            .execution_options(synchronize_session=False)
        )

        # No row updated: distinguish 404 from 409.
        if result.rowcount == 0:
            document = (
                db.query(Document)
                .filter(Document.id == document_id)
                .first()
            )

            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found."
                )

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Document has already been reviewed."
            )

        # Fetch the updated document.
        document = (
            db.query(Document)
            .filter(Document.id == document_id)
            .first()
        )

        # Update associated workflow status.
        update_workflow_approval_status(
            db,
            document.workflow_id
        )

        db.commit()
        db.refresh(document)

        return document

    except Exception:
        db.rollback()
        raise
