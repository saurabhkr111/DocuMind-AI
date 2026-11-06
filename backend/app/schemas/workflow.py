from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, ConfigDict, Field


# -----------------------------------------
# CREATE WORKFLOW
# -----------------------------------------

class WorkflowCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    source_type: Optional[str] = None
    source_reference: Optional[str] = None


# -----------------------------------------
# BASIC WORKFLOW RESPONSE
# -----------------------------------------

class WorkflowResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------
# UPDATE WORKFLOW
# -----------------------------------------

class WorkflowUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None

    status: Optional[
        Literal[
            "PENDING",
            "RUNNING",
            "COMPLETED",
            "AWAITING_APPROVAL",
            "APPROVED",
            "REJECTED",
            "PARTIAL",
            "FAILED"
        ]
    ] = None


# -----------------------------------------
# AGENT LOG RESPONSE
# -----------------------------------------

class AgentLogResponse(BaseModel):
    id: int
    agent_name: str
    status: str
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------
# GENERATED DOCUMENT RESPONSE
# -----------------------------------------

class DocumentResponse(BaseModel):
    id: int
    title: str
    document_type: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------
# COMPLETE WORKFLOW HISTORY RESPONSE
# -----------------------------------------

class WorkflowDetailResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str

    source_type: Optional[str] = None
    source_reference: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    agent_logs: list[AgentLogResponse] = Field(
        default_factory=list
    )

    documents: list[DocumentResponse] = Field(
        default_factory=list
    )

    model_config = ConfigDict(from_attributes=True)