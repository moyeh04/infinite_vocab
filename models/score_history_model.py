"""Pydantic model for a score history entry."""

from datetime import datetime

from pydantic import BaseModel, Field


class ScoreHistoryEntry(BaseModel):
    """Represents a single score change event."""

    entry_id: str = Field(alias="entryId")
    user_id: str = Field(alias="userId")
    admin_id: str = Field(alias="adminId")
    score_change: int = Field(alias="scoreChange")
    new_total_score: int = Field(alias="newTotalScore")
    reason: str
    created_at: datetime = Field(alias="createdAt")

    class Config:
        populate_by_name = True
