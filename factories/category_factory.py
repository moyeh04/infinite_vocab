"""Category Factory - Business Logic for Category objects"""

from models import Category
from schemas import CategoryCreateSchema, CategoryUpdateSchema
from utils import ValidationError


class CategoryFactory:
    """Factory for creating Category objects with business rules."""

    @staticmethod
    def create_from_schema(schema: CategoryCreateSchema, user_id: str) -> Category:
        """Create Category from validated schema with business rules applied."""
        normalized_name = CategoryFactory._normalize_category_name(schema.category_name)
        validated_color = CategoryFactory._validate_color_format(schema.category_color)

        return Category(
            category_name=normalized_name,
            category_color=validated_color,
            user_id=user_id,
        )

    @staticmethod
    def create_update_dict(schema: CategoryUpdateSchema) -> dict:
        """Create update dictionary from validated schema with business rules applied."""
        updates = {}

        if schema.category_name is not None:
            updates["category_name"] = CategoryFactory._normalize_category_name(
                schema.category_name
            )

        if schema.category_color is not None:
            updates["category_color"] = CategoryFactory._validate_color_format(
                schema.category_color
            )

        return updates

    @staticmethod
    def _normalize_category_name(name: str) -> str:
        """Business rule: title case and trimmed."""
        return name.strip().title()

    @staticmethod
    def _validate_color_format(color: str) -> str:
        """Business rule: validate hex color format (6 characters)."""
        color = color.strip().lower()

        if not color.startswith("#"):
            raise ValidationError("Color must be a valid hex color (e.g., #FF5733)")

        if len(color) != 7 or not all(c in "0123456789abcdef" for c in color[1:]):
            raise ValidationError("Hex color must be 6 characters (e.g., #FF5733)")

        return color
