"""Word-Category Service Layer"""

import logging
from typing import List

from data_access import category_dal as c_dal
from data_access import word_category_dal as wc_dal
from data_access import word_dal as w_dal
from utils import DatabaseError, DuplicateEntryError, NotFoundError, WordServiceError

logger = logging.getLogger("infinite_vocab_app")


def add_word_to_category(db, user_id: str, category_id: str, word_id: str) -> dict:
    """Orchestrates adding a word to a category and returns a descriptive success message."""
    logger.info(
        f"SERVICE: Linking word {word_id} to category {category_id} for user {user_id}."
    )
    try:
        word_model = w_dal.get_word_by_id(db, word_id)
        if not word_model or word_model.user_id != user_id:
            raise NotFoundError("Word not found or access is forbidden.")

        category = c_dal.get_category_by_id(db, category_id)
        if not category or category.user_id != user_id:
            raise NotFoundError("Category not found or access is forbidden.")

        if wc_dal.check_link_exists(db, word_id, category_id):
            raise DuplicateEntryError("Word is already in this category.")

        wc_dal.link_word_to_category(db, user_id, word_id, category_id)

        word_name = word_model.word_text
        category_name = category.category_name
        logger.info(
            f"SERVICE: Successfully linked word '{word_name}' to category '{category_name}'."
        )
        return {
            "message": f"Word '{word_name}' successfully added to category '{category_name}'."
        }

    except (NotFoundError, DuplicateEntryError) as e:
        logger.warning(
            f"SERVICE: Client error linking word {word_id} to category {category_id}: {e}"
        )
        raise
    except DatabaseError as e:
        logger.error(
            f"SERVICE: DatabaseError linking word {word_id} to category {category_id}: {e}"
        )
        raise WordServiceError(
            "A database error occurred while linking the word to the category."
        ) from e


def remove_word_from_category(db, user_id: str, category_id: str, word_id: str) -> dict:
    """Orchestrates removing a word from a category and returns a descriptive success message."""
    logger.info(
        f"SERVICE: Unlinking word {word_id} from category {category_id} for user {user_id}."
    )
    try:
        word_model = w_dal.get_word_by_id(db, word_id)
        if not word_model or word_model.user_id != user_id:
            raise NotFoundError("Word not found or access is forbidden.")

        category = c_dal.get_category_by_id(db, category_id)
        if not category or category.user_id != user_id:
            raise NotFoundError("Category not found or access is forbidden.")

        if not wc_dal.check_link_exists(db, word_id, category_id):
            raise NotFoundError("This word is not in the specified category.")

        wc_dal.unlink_word_from_category(db, word_id, category_id)

        word_name = word_model.word_text
        category_name = category.category_name
        logger.info(
            f"SERVICE: Successfully unlinked word '{word_name}' from category '{category_name}'."
        )
        return {
            "message": f"Word '{word_name}' successfully removed from category '{category_name}'."
        }

    except NotFoundError as e:
        logger.warning(
            f"SERVICE: NotFound error unlinking word {word_id} from category {category_id}: {e}"
        )
        raise
    except DatabaseError as e:
        logger.error(
            f"SERVICE: DatabaseError unlinking word {word_id} from category {category_id}: {e}"
        )

        raise WordServiceError(
            "A database error occurred while unlinking the word from the category."
        ) from e


def get_words_for_category(db, user_id: str, category_id: str) -> List[dict]:
    """Gets all words belonging to a specific category for a user."""
    logger.info(
        f"SERVICE: Getting words for category {category_id} for user {user_id}."
    )
    try:
        category = c_dal.get_category_by_id(db, category_id)
        if not category or category.user_id != user_id:
            raise NotFoundError("Category not found or access is forbidden.")

        word_ids = wc_dal.get_word_ids_by_category_id(db, category_id)
        if not word_ids:
            return []

        words_list = []
        for word_id in word_ids:
            word_model = w_dal.get_word_by_id(db, word_id)
            if word_model and word_model.user_id == user_id:
                # Convert Word model to dict for backward compatibility
                word_data = word_model.model_dump(by_alias=True)
                words_list.append(word_data)

        logger.info(
            f"SERVICE: Found {len(words_list)} words for category {category_id}."
        )
        return words_list

    except NotFoundError as e:
        logger.warning(
            f"SERVICE: NotFound error getting words for category {category_id}: {e}"
        )
        raise
    except DatabaseError as e:
        logger.error(
            f"SERVICE: DatabaseError getting words for category {category_id}: {e}"
        )
        raise WordServiceError(
            "A database error occurred while retrieving words for the category."
        ) from e
