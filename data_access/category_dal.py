"""Category Data Access Layer"""

import logging
from typing import List, Optional

from firebase_admin import firestore

from models import Category
from utils import DatabaseError, timed_execution

logger = logging.getLogger("infinite_vocab_app")


@timed_execution(logger, "Category Creation")
def create_category(db, category: Category) -> Category:
    """Save category and return with ID and timestamp."""
    logger.info(
        f"DAL: Creating category '{category.category_name}' for user {category.user_id}."
    )
    try:
        category_data = {
            "user_id": category.user_id,
            "category_name": category.category_name,
            "category_name_search": category.category_name_search,  # Include search field
            "category_color": category.category_color,
            "createdAt": firestore.SERVER_TIMESTAMP,
        }
        logger.debug(
            f"DAL: Adding document to collection='categories' with data={category_data}"
        )
        doc_ref = db.collection("categories").add(category_data)[1]
        saved_doc = doc_ref.get()
        saved_data = saved_doc.to_dict()

        logger.info(f"DAL: Successfully created category with ID: {doc_ref.id}")
        saved_data["category_id"] = doc_ref.id
        return Category.model_validate(saved_data)

    except Exception as e:
        logger.error(
            f"DAL: Failed to create category for user {category.user_id}: {e}",
            exc_info=True,
        )
        raise DatabaseError(f"Failed to create category: {str(e)}") from e


@timed_execution(logger, "Category Listing")
def get_categories_by_user(db, user_id: str) -> List[Category]:
    """Get all categories for user."""
    logger.info(f"DAL: Getting categories for user {user_id}.")
    try:
        query = (
            db.collection("categories")
            .where("user_id", "==", user_id)
            .order_by("category_name")
        )
        docs = query.stream()

        categories = []
        for doc in docs:
            data = doc.to_dict()
            data["category_id"] = doc.id

            categories.append(Category.model_validate(data))

        logger.info(f"DAL: Found {len(categories)} categories for user {user_id}.")
        return categories
    except Exception as e:
        logger.error(
            f"DAL: Failed to get categories for user {user_id}: {e}", exc_info=True
        )
        raise DatabaseError(f"Failed to get categories: {str(e)}") from e


def get_category_by_id(db, category_id: str) -> Optional[Category]:
    """Get category by ID."""
    logger.info(f"DAL: Getting category by ID: {category_id}.")
    try:
        doc = db.collection("categories").document(category_id).get()
        if not doc.exists:
            logger.warning(f"DAL: Category with ID {category_id} not found.")
            return None

        data = doc.to_dict()
        data["category_id"] = doc.id
        return Category.model_validate(data)
    except Exception as e:
        logger.error(f"DAL: Failed to get category {category_id}: {e}", exc_info=True)
        raise DatabaseError(f"Failed to get category: {str(e)}") from e


@timed_execution(logger, "Category Update")
def update_category(db, category_id: str, updates: dict) -> Optional[Category]:
    """Update category fields."""
    logger.info(
        f"DAL: Updating category {category_id} with keys: {list(updates.keys())}"
    )
    try:
        doc_ref = db.collection("categories").document(category_id)
        if not doc_ref.get().exists:
            logger.warning(f"DAL: Category {category_id} not found for update.")
            return None

        updates["updatedAt"] = firestore.SERVER_TIMESTAMP
        doc_ref.update(updates)

        updated_doc = doc_ref.get()
        logger.info(f"DAL: Successfully updated category {category_id}.")
        data = updated_doc.to_dict()
        data["category_id"] = doc_ref.id
        return Category.model_validate(data)
    except Exception as e:
        logger.error(
            f"DAL: Failed to update category {category_id}: {e}", exc_info=True
        )
        raise DatabaseError(f"Failed to update category: {str(e)}") from e


@timed_execution(logger, "Category Deletion")
def delete_category(db, category_id: str) -> bool:
    """Delete category by ID."""
    logger.info(f"DAL: Deleting category {category_id}.")
    try:
        doc_ref = db.collection("categories").document(category_id)
        if not doc_ref.get().exists:
            logger.warning(f"DAL: Category {category_id} not found for deletion.")
            return False

        doc_ref.delete()
        logger.info(f"DAL: Successfully deleted category {category_id}.")
        return True
    except Exception as e:
        logger.error(
            f"DAL: Failed to delete category {category_id}: {e}", exc_info=True
        )
        raise DatabaseError(f"Failed to delete category: {str(e)}") from e
