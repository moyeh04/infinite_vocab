from pydantic import BaseModel, Field


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
        # Example for API documentation (Request Example)
        json_schema_extra = {
            "title": "Category Creation Request",
            "description": "Schema for creating a new vocabulary category",
            "example": {"category_name": "Science Terms", "category_color": "#4A90E2"},
        }
