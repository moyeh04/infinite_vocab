# Schemas package - Pydantic schemas for request validation

from .admin_schema import RoleUpdateSchema
from .category_schema import CategoryCreateSchema, CategoryUpdateSchema
from .score_update_schema import ScoreUpdateSchema
from .user_schema import UserCreateSchema, UserUpdateSchema
from .word_schemas import (
    WordCreateSchema,
    WordUpdateSchema,
    WordExistenceCheckSchema,
    DescriptionCreateSchema,
    DescriptionUpdateSchema,
    ExampleCreateSchema,
    ExampleUpdateSchema,
)

__all__ = [
    "RoleUpdateSchema",
    "CategoryCreateSchema",
    "CategoryUpdateSchema",
    "UserCreateSchema",
    "UserUpdateSchema",
    "ScoreUpdateSchema",
    "WordCreateSchema",
    "WordUpdateSchema",
    "WordExistenceCheckSchema",
    "DescriptionCreateSchema",
    "DescriptionUpdateSchema",
    "ExampleCreateSchema",
    "ExampleUpdateSchema",
]
