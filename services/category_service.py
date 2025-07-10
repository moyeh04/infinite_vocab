"""Category service - Business logic and validation for category operations"""

from typing import List

from data_access import category_dal
from factories.category_factory import CategoryFactory
from models import Category
from schemas import CategoryCreateSchema, CategoryUpdateSchema
from utils import (
    CategoryServiceError,
    DatabaseError,
    NotFoundError,
)


def create_category(db, user_id: str, schema: CategoryCreateSchema) -> Category:
    """Creates a new category for a user with duplicate validation"""
    try:
        # Check for duplicate category name for this user
        existing_categories = category_dal.get_categories_by_user(db, user_id)
        normalized_name = schema.category_name.strip().lower()

        for existing_category in existing_categories:
            if existing_category.category_name.lower() == normalized_name:
                raise CategoryServiceError(
                    f"Category '{schema.category_name}' already exists for this user."
                )

        # Use Factory to create partial Category with business validation
        partial_category = CategoryFactory.create_from_schema(schema, user_id)

        # Use DAL to persist and get complete Category with real ID/timestamps
        created_category = category_dal.create_category(db, partial_category)
        return created_category

    except DatabaseError as de:
        print(
            f"CategoryService: DatabaseError during category creation for user '{user_id}': {str(de)}"
        )
        raise CategoryServiceError(
            f"Could not create category '{schema.category_name}' due to a database issue."
        ) from de
    except Exception as e:
        print(
            f"CategoryService: Unexpected error during category creation for user '{user_id}': {str(e)}"
        )
        raise CategoryServiceError(
            "An unexpected error occurred while creating the category."
        ) from e


def get_categories_by_user(db, user_id: str) -> List[Category]:
    """Retrieves all categories for a user, sorted alphabetically"""
    try:
        categories = category_dal.get_categories_by_user(db, user_id)
        return categories

    except DatabaseError as de:
        print(
            f"CategoryService: DatabaseError during category retrieval for user '{user_id}': {str(de)}"
        )
        raise CategoryServiceError(
            "Could not retrieve categories due to a database issue."
        ) from de
    except Exception as e:
        print(
            f"CategoryService: Unexpected error during category retrieval for user '{user_id}': {str(e)}"
        )
        raise CategoryServiceError(
            "An unexpected error occurred while retrieving categories."
        ) from e


def get_category_by_id(db, category_id: str, user_id: str) -> Category:
    """Retrieves a category by ID with user ownership validation"""
    try:
        category = category_dal.get_category_by_id(db, category_id)

        # Check if category exists
        if not category:
            raise NotFoundError(f"Category with ID '{category_id}' not found.")

        # Validate user ownership
        if category.user_id != user_id:
            raise NotFoundError(f"Category with ID '{category_id}' not found.")

        return category
    except DatabaseError as de:
        print(
            f"CategoryService: DatabaseError during category retrieval for ID '{category_id}': {str(de)}"
        )
        raise CategoryServiceError(
            "Could not retrieve category due to a database issue."
        ) from de
    except Exception as e:
        print(
            f"CategoryService: Unexpected error during category retrieval for ID '{category_id}': {str(e)}"
        )
        raise CategoryServiceError(
            "An unexpected error occurred while retrieving the category."
        ) from e


def update_category(
    db, category_id: str, user_id: str, schema: CategoryUpdateSchema
) -> Category:
    """Updates a category with user validation and duplicate checking"""
    try:
        # First verify the category exists and belongs to user
        existing_category = get_category_by_id(db, category_id, user_id)

        # Use Factory to create validated update dictionary
        updates = CategoryFactory.create_update_dict(schema)

        if not updates:
            # No valid updates provided, return existing category
            return existing_category

        # If updating name, check for duplicates
        if "category_name" in updates:
            new_name = updates["category_name"].lower()
            current_name = existing_category.category_name.lower()

            if new_name != current_name:
                user_categories = category_dal.get_categories_by_user(db, user_id)
                for category in user_categories:
                    if (
                        category.category_id != category_id
                        and category.category_name.lower() == new_name
                    ):
                        raise CategoryServiceError(
                            f"Category '{updates['category_name']}' already exists for this user."
                        )

        # Use DAL to update and return updated category
        updated_category = category_dal.update_category(db, category_id, updates)
        return updated_category
    except (NotFoundError, CategoryServiceError):
        # Re-raise application errors as-is
        raise
    except DatabaseError as de:
        print(
            f"CategoryService: DatabaseError during category update for ID '{category_id}': {str(de)}"
        )
        raise CategoryServiceError(
            "Could not update category due to a database issue."
        ) from de


def delete_category(db, category_id: str, user_id: str) -> None:
    """Deletes a category with user ownership validation"""
    try:
        # First verify the category exists and belongs to user
        get_category_by_id(db, category_id, user_id)

        # Use DAL to delete - check if deletion was successful
        deleted = category_dal.delete_category(db, category_id)

        if not deleted:
            raise NotFoundError(f"Category with ID '{category_id}' not found.")

    except (NotFoundError, CategoryServiceError):
        # Re-raise application errors as-is
        raise
    except DatabaseError as de:
        print(
            f"CategoryService: DatabaseError during category deletion for ID '{category_id}': {str(de)}"
        )
        raise CategoryServiceError(
            "Could not delete category due to a database issue."
        ) from de
    except Exception as e:
        print(
            f"CategoryService: Unexpected error during category deletion for ID '{category_id}': {str(e)}"
        )
        raise CategoryServiceError(
            "An unexpected error occurred while deleting the category."
        ) from e
