"""Category service - Business logic and validation for category operations"""

import logging
from typing import List

from data_access import category_dal as c_dal
from factories.category_factory import CategoryFactory
from models import Category
from schemas import CategoryCreateSchema, CategoryUpdateSchema
from utils import CategoryServiceError, DatabaseError, NotFoundError

logger = logging.getLogger("infinite_vocab_app")


def create_category(db, user_id: str, schema: CategoryCreateSchema) -> Category:
    """Creates a new category for a user with duplicate validation"""
    logger.info(
        f"SERVICE: create_category invoked for user '{user_id}' with name '{schema.category_name}'."
    )
    try:
        existing_categories = c_dal.get_categories_by_user(db, user_id)
        normalized_name = schema.category_name.strip().lower()

        for existing_category in existing_categories:
            if existing_category.category_name.lower() == normalized_name:
                raise CategoryServiceError(
                    f"Category '{schema.category_name}' already exists for this user."
                )

        partial_category = CategoryFactory.create_from_schema(schema, user_id)
        created_category = c_dal.create_category(db, partial_category)
        logger.info(
            f"SERVICE: Successfully created category '{created_category.category_id}' for user '{user_id}'."
        )
        return created_category
    except DatabaseError as e:
        logger.error(
            f"SERVICE: DatabaseError during category creation for user '{user_id}': {e}"
        )
        raise CategoryServiceError(
            f"Could not create category '{schema.category_name}' due to a database issue."
        ) from e
    except Exception as e:
        logger.error(
            f"SERVICE: Unexpected error during category creation for user '{user_id}': {e}",
            exc_info=True,
        )
        raise


def get_categories_by_user(db, user_id: str) -> List[Category]:
    """Retrieves all categories for a user, sorted alphabetically"""
    logger.info(f"SERVICE: get_categories_by_user invoked for user '{user_id}'.")
    try:
        categories = c_dal.get_categories_by_user(db, user_id)
        return categories
    except DatabaseError as e:
        logger.error(
            f"SERVICE: DatabaseError during category retrieval for user '{user_id}': {e}"
        )
        raise CategoryServiceError(
            "Could not retrieve categories due to a database issue."
        ) from e


def get_category_by_id(db, category_id: str, user_id: str) -> Category:
    """Retrieves a category by ID with user ownership validation"""
    logger.info(
        f"SERVICE: get_category_by_id invoked for cat '{category_id}' by user '{user_id}'."
    )
    try:
        category = c_dal.get_category_by_id(db, category_id)
        if not category:
            raise NotFoundError(f"Category with ID '{category_id}' not found.")
        if category.user_id != user_id:
            logger.warning(
                f"SERVICE: Ownership check failed for cat '{category_id}'. Requester: '{user_id}', Owner: '{category.user_id}'."
            )
            raise NotFoundError(f"Category with ID '{category_id}' not found.")
        return category
    except DatabaseError as e:
        logger.error(
            f"SERVICE: DatabaseError during get_category_by_id for '{category_id}': {e}"
        )
        raise CategoryServiceError(
            "Could not retrieve category due to a database issue."
        ) from e


def update_category(
    db, category_id: str, user_id: str, schema: CategoryUpdateSchema
) -> Category:
    """Updates a category with user validation and duplicate checking"""
    logger.info(
        f"SERVICE: update_category invoked for cat '{category_id}' by user '{user_id}'."
    )
    try:
        existing_category = get_category_by_id(db, category_id, user_id)
        updates = CategoryFactory.create_update_dict(schema)
        if not updates:
            return existing_category

        if "category_name" in updates:
            new_name = updates["category_name"].lower()
            if new_name != existing_category.category_name.lower():
                user_categories = c_dal.get_categories_by_user(db, user_id)
                for cat in user_categories:
                    if (
                        cat.category_id != category_id
                        and cat.category_name.lower() == new_name
                    ):
                        raise CategoryServiceError(
                            f"Category '{updates['category_name']}' already exists."
                        )

        updated_category = c_dal.update_category(db, category_id, updates)
        logger.info(f"SERVICE: Successfully updated category '{category_id}'.")
        return updated_category
    except (NotFoundError, CategoryServiceError):
        raise
    except DatabaseError as e:
        logger.error(
            f"SERVICE: DatabaseError during category update for '{category_id}': {e}"
        )
        raise CategoryServiceError(
            "Could not update category due to a database issue."
        ) from e


def delete_category(db, category_id: str, user_id: str) -> None:
    """Deletes a category with user ownership validation"""
    logger.info(
        f"SERVICE: delete_category invoked for cat '{category_id}' by user '{user_id}'."
    )
    try:
        get_category_by_id(db, category_id, user_id)
        deleted = c_dal.delete_category(db, category_id)
        if not deleted:
            raise NotFoundError(
                f"Category with ID '{category_id}' not found for deletion."
            )
    except (NotFoundError, CategoryServiceError):
        raise
    except DatabaseError as e:
        logger.error(
            f"SERVICE: DatabaseError during category deletion for '{category_id}': {e}"
        )
        raise CategoryServiceError(
            "Could not delete category due to a database issue."
        ) from e
