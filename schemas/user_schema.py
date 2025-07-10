"""Pydantic schemas for user-related API requests."""

from typing import Optional

from pydantic import BaseModel, Field


class UserCreateSchema(BaseModel):
    """Schema for validating user creation/registration requests."""

    # This field is required when a user first signs in.
    # The alias 'userName' allows the frontend to send camelCase.
    user_name: str = Field(
        alias="userName",
        min_length=1,
        max_length=50,
        strip_whitespace=True,
        description="The user's display name",
    )

    class Config:
        # Allow Pydantic to populate the model using either field names or aliases
        populate_by_name = True
        # Provide an example for API documentation tools

        json_schema_extra = {
            "title": "User Creation Request",
            "description": "Schema for registering a user or retrieving their initial code.",
            "example": {"userName": "John Doe"},
        }


class UserUpdateSchema(BaseModel):
    """Schema for validating user update requests."""

    # This field is optional for partial updates (e.g., PATCH requests).
    user_name: Optional[str] = Field(
        None,
        alias="userName",
        min_length=1,
        max_length=50,
        strip_whitespace=True,
        description="The user's new display name",
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "title": "User Update Request",
            "description": "Schema for updating a user's profile information.",
            "example": {"userName": "Jonathan Doe"},
        }
