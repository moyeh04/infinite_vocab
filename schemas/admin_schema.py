"""Pydantic schemas for admin-specific API requests."""

from pydantic import BaseModel, Field


class RoleUpdateSchema(BaseModel):
    """Schema for validating an admin role update request."""

    role: str = Field(
        min_length=1,
        max_length=50,
        strip_whitespace=True,
        description="The new role to assign to the admin (e.g., 'super-admin', 'moderator').",
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {"role": "super-admin"},
        }
