from typing import Optional, Literal

from pydantic import BaseModel, ConfigDict, Field


# Schema for creating a new workflow
class WorkflowCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    source_type: Optional[str] = None
    source_reference: Optional[str] = None


# Schema for returning workflow information
class WorkflowResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str

    model_config = ConfigDict(from_attributes=True)


# Schema for updating an existing workflow
class WorkflowUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None

    status: Optional[
        Literal[
            "PENDING",
            "RUNNING",
            "AWAITING_APPROVAL",
            "APPROVED",
            "REJECTED",
            "PARTIAL",
            "FAILED"
        ]
    ] = None