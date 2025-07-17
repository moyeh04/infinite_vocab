"""Category Factory - Business Logic for Category objects"""

import logging

from models import Category
from schemas import CategoryCreateSchema, CategoryUpdateSchema
from utils import ValidationError

logger = logging.getLogger("infinite_vocab_app")


class CategoryFactory:
    """Factory for creating Category objects with business rules."""

    @staticmethod
    def create_from_schema(schema: CategoryCreateSchema, user_id: str) -> Category:
        """Create Category from validated schema with business rules applied."""
        logger.info(
            f"FACTORY: Creating new category model from schema for user: {user_id}"
        )
        normalized_name = CategoryFactory._normalize_category_name(schema.category_name)
        validated_color = CategoryFactory._validate_color_format(schema.category_color)

        return Category(
            category_name=normalized_name,
            category_name_search=normalized_name.lower(),  # Lowercase version for searching
            category_color=validated_color,
            user_id=user_id,
        )

    @staticmethod
    def create_update_dict(schema: CategoryUpdateSchema) -> dict:
        """Create update dictionary from validated schema with business rules applied."""
        updates = {}

        if schema.category_name is not None:
            normalized_name = CategoryFactory._normalize_category_name(
                schema.category_name
            )
            updates["category_name"] = normalized_name
            updates["category_name_search"] = (
                normalized_name.lower()
            )  # Lowercase version for searching

        if schema.category_color is not None:
            updates["category_color"] = CategoryFactory._validate_color_format(
                schema.category_color
            )

        logger.info(
            f"FACTORY: Created category update dictionary with keys: {list(updates.keys())}"
        )
        return updates

    @staticmethod
    def _normalize_category_name(name: str) -> str:
        """Normalize category name by trimming whitespace, preserving original capitalization."""
        return name.strip()

    @staticmethod
    def _validate_color_format(color: str) -> str:
        """Business rule: validate hex color format (6 characters)."""
        color = color.strip()
        # Convert to lowercase only for validation, but preserve original case for storage
        if not color.lower().startswith("#") or len(color) != 7:
            raise ValidationError(
                "Color must be a valid hex color starting with # (e.g., #FF5733)"
            )

        return color
