from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Category(BaseModel):
    """Category data model for responses and internal operations"""

    category_id: Optional[str] = Field(alias="categoryId", default=None)
    user_id: str = Field(alias="userId")
    category_name: str = Field(alias="categoryName")
    category_color: str = Field(alias="categoryColor", default="#FFFFFF")
    created_at: Optional[datetime] = Field(alias="createdAt", default=None)
    updated_at: Optional[datetime] = Field(alias="updatedAt", default=None)

    class Config:
        # Serialization rules - convert Python types to JSON-safe types
        json_encoders = {
            datetime: lambda dt: dt.isoformat()  # Convert datetime → ISO string
        }

        # Allow both snake_case and camelCase field names
        validate_by_name = True

        # Example for API documentation (Response Example)

        json_schema_extra = {
            "example": {
                "categoryId": "cat_12345",
                "userId": "user_67890",
                "categoryName": "Science Terms",
                "categoryColor": "#4A90E2",
                "createdAt": "2025-07-10T14:30:00",
                "updatedAt": None,
            }
        }
