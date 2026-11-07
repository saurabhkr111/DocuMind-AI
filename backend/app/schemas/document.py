from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# -----------------------------------------
# DOCUMENT RESPONSE
# -----------------------------------------

class DocumentResponse(BaseModel):

    id: int
    workflow_id: int
    title: str
    document_type: str
    content: str
    created_at: datetime

    approval_status: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    approval_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------
# DOCUMENT APPROVAL REQUEST
# -----------------------------------------

class DocumentApprovalRequest(BaseModel):
    """
    Approval payload.

    `reviewed_by` is optional for backward compatibility and is ignored.
    The stored reviewer is always taken from the authenticated principal.
    """

    reviewed_by: Optional[str] = Field(
        default=None,
        max_length=255,
    )

    @field_validator("reviewed_by")
    @classmethod
    def validate_reviewer(cls, value: Optional[str]) -> Optional[str]:

        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        return value


# -----------------------------------------
# DOCUMENT REJECTION REQUEST
# -----------------------------------------

class DocumentRejectionRequest(BaseModel):
    """
    Rejection payload.

    `reviewed_by` is optional for backward compatibility and is ignored.
    The stored reviewer is always taken from the authenticated principal.
    """

    reviewed_by: Optional[str] = Field(
        default=None,
        max_length=255,
    )

    reason: str = Field(
        ...,
        min_length=5,
        max_length=2000
    )

    @field_validator("reviewed_by")
    @classmethod
    def validate_reviewer(cls, value: Optional[str]) -> Optional[str]:

        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        return value

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:

        value = value.strip()

        if not value:
            raise ValueError("Rejection reason cannot be empty.")

        return value
