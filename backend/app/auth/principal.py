from pydantic import BaseModel, Field


class Principal(BaseModel):
    """Authenticated caller identity used for authorization and audit fields."""

    name: str = Field(..., min_length=1, max_length=255)
