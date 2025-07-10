from pydantic import BaseModel, Field
from typing import Optional


class CategoryCreateSchema(BaseModel):
    """Schema for validating category creation requests"""

    # Accepts camelCase field names from frontend requests via aliases

    category_name: str = Field(
        alias="categoryName",
        min_length=1,
        max_length=50,
        strip_whitespace=True,
        description="Name of the category",
    )

    category_color: str = Field(
        alias="categoryColor",
        pattern=r"#[0-9A-Fa-f]{6}$",
        description="Hex color code (e.g., #FF5733)",
    )

    class Config:
        # Allow both snake_case and camelCase field names
        populate_by_name = True
        # Example for API documentation (Request Example)
        json_schema_extra = {
            "title": "Category Creation Request",
            "description": "Schema for creating a new vocabulary category",
            "example": {"categoryName": "Science Terms", "categoryColor": "#4A90E2"},
        }


class CategoryUpdateSchema(BaseModel):
    """Schema for validating category update requests"""

    # Optional fields for partial updates
    category_name: Optional[str] = Field(
        None,
        alias="categoryName",
        min_length=1,
        max_length=50,
        strip_whitespace=True,
        description="Name of the category",
    )

    category_color: Optional[str] = Field(
        None,
        alias="categoryColor",
        pattern=r"#[0-9A-Fa-f]{6}$",
        description="Hex color code (e.g., #FF5733)",
    )

    class Config:
        # Allow both snake_case and camelCase field names
        populate_by_name = True
        json_schema_extra = {
            "title": "Category Update Request",
            "description": "Schema for updating an existing vocabulary category",
            "example": {"categoryName": "Updated Science Terms"},
        }
