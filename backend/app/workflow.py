from pydantic import BaseModel
from typing import Optional


class WorkflowCreate(BaseModel):
    title: str
    description: Optional[str] = None
    source_type: Optional[str] = None
    source_reference: Optional[str] = None


class WorkflowResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str

    class Config:
        from_attributes = True