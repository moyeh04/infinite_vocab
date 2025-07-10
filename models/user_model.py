"""User data model for responses and internal operations."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class User(BaseModel):
    """Represents a user in the system."""

    # Note: All fields use an alias for seamless snake_case <-> camelCase conversion.
    user_id: Optional[str] = Field(alias="userId", default=None)
    user_name: str = Field(alias="userName")
    user_code: str = Field(alias="userCode")
    total_score: int = Field(alias="totalScore", default=0)
    created_at: Optional[datetime] = Field(alias="createdAt", default=None)
    updated_at: Optional[datetime] = Field(alias="updatedAt", default=None)

    class Config:
        # Allow creating the model from dicts with either snake_case or camelCase keys
        populate_by_name = True
        # Define how to convert complex types to JSON
        json_encoders = {
            datetime: lambda dt: dt.isoformat()  # Convert datetime to ISO string
        }
        # Provide an example for API documentation
        json_schema_extra = {
            "example": {
                "userId": "firebase_user_id_abc123",
                "userName": "Jane Doe",
                "userCode": "ABC12345",
                "totalScore": 150,
                "createdAt": "2025-07-10T12:00:00",
                "updatedAt": "2025-07-10T14:30:00",
            }
        }
