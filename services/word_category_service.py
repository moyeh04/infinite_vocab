"""Word-Category Service Layer"""

from typing import List

from data_access import category_dal as c_dal
from data_access import word_category_dal as wc_dal
from data_access import word_dal as w_dal
from utils import DatabaseError, DuplicateEntryError, NotFoundError, WordServiceError


def add_word_to_category(db, user_id: str, category_id: str, word_id: str) -> dict:
    """Orchestrates adding a word to a category and returns a descriptive success message."""
    # ... function logic is unchanged

    try:
        # 1. Verify word exists and is owned by user
        word_doc = w_dal.get_word_by_id(db, word_id)
        if not word_doc.exists or word_doc.to_dict().get("user_id") != user_id:
            raise NotFoundError("Word not found or access is forbidden.")

        # 2. Verify category exists and is owned by user
        category = c_dal.get_category_by_id(db, category_id)
        if not category or category.user_id != user_id:
            raise NotFoundError("Category not found or access is forbidden.")

        # 3. Check if the link already exists to prevent duplicates
        if wc_dal.check_link_exists(db, word_id, category_id):
            raise DuplicateEntryError("Word is already in this category.")

        # 4. If all checks pass, create the link
        wc_dal.link_word_to_category(db, user_id, word_id, category_id)

        # 5. Prepare and return a descriptive success message
        word_name = word_doc.to_dict().get("word_text", "word")
        category_name = category.category_name

        return {
            "message": f"Word '{word_name}' successfully added to category '{category_name}'."
        }
    except (NotFoundError, DuplicateEntryError):
        raise
    except DatabaseError as e:
        raise WordServiceError(
            "A database error occurred while linking the word to the category."
        ) from e


def remove_word_from_category(db, user_id: str, category_id: str, word_id: str) -> dict:
    """Orchestrates removing a word from a category and returns a descriptive success message."""
    # ... function logic is unchanged
    try:
        # 1. Verify word exists and is owned by user
        word_doc = w_dal.get_word_by_id(db, word_id)
        if not word_doc.exists or word_doc.to_dict().get("user_id") != user_id:
            raise NotFoundError("Word not found or access is forbidden.")

        # 2. Verify category exists and is owned by user
        category = c_dal.get_category_by_id(db, category_id)
        if not category or category.user_id != user_id:
            raise NotFoundError("Category not found or access is forbidden.")

        # 3. Check that the link exists before attempting to delete
        if not wc_dal.check_link_exists(db, word_id, category_id):
            raise NotFoundError("This word is not in the specified category.")

        # 4. If the link exists, proceed with deletion
        wc_dal.unlink_word_from_category(db, word_id, category_id)

        # 5. Prepare and return a descriptive success message
        word_name = word_doc.to_dict().get("word_text", "word")

        category_name = category.category_name

        return {
            "message": f"Word '{word_name}' successfully removed from category '{category_name}'."
        }
    except NotFoundError:
        raise

    except DatabaseError as e:
        raise WordServiceError(
            "A database error occurred while unlinking the word from the category."
        ) from e


def get_words_for_category(db, user_id: str, category_id: str) -> List[dict]:
    """
    Gets all words belonging to a specific category for a user.
    """
    # ... function logic is unchanged
    try:
        # 1. Verify category exists and is owned by user to authorize access
        category = c_dal.get_category_by_id(db, category_id)
        if not category or category.user_id != user_id:
            raise NotFoundError("Category not found or access is forbidden.")

        # 2. Get all linked word IDs from the linking collection
        word_ids = wc_dal.get_word_ids_by_category_id(db, category_id)
        if not word_ids:
            return []  # Return empty list if no words are in the category

        # 3. Fetch full details for each word
        words_list = []
        for word_id in word_ids:
            word_doc = w_dal.get_word_by_id(db, word_id)
            if word_doc.exists:
                word_data = word_doc.to_dict()
                if word_data.get("user_id") == user_id:
                    word_data["word_id"] = word_doc.id
                    words_list.append(word_data)

        return words_list

    except NotFoundError:
        raise

    except DatabaseError as e:
        raise WordServiceError(
            "A database error occurred while retrieving words for the category."
        ) from e
