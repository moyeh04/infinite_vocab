"""Pydantic schema for the admin score update request."""

from pydantic import BaseModel, Field


class ScoreUpdateSchema(BaseModel):
    """Schema for validating a score update."""

    score_change: int = Field(alias="scoreChange")
    reason: str = Field(min_length=1, max_length=200)

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {"scoreChange": 10, "reason": "Completed weekly assessment."}
        }
