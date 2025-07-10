"""Word-Category Link Data Access Layer"""

import logging
from typing import List

from firebase_admin import firestore

from utils import DatabaseError

logger = logging.getLogger("infinite_vocab_app")


def link_word_to_category(db, user_id: str, word_id: str, category_id: str) -> None:
    """Creates a link document between a word and a category."""
    link_id = f"{word_id}_{category_id}"
    logger.info(
        f"DAL: Linking word {word_id} to category {category_id} with link_id {link_id}."
    )
    try:
        link_ref = db.collection("word_categories").document(link_id)

        link_ref.set(
            {
                "word_id": word_id,
                "category_id": category_id,
                "user_id": user_id,
                "createdAt": firestore.SERVER_TIMESTAMP,
            }
        )
    except Exception as e:
        logger.error(
            f"DAL: Failed to link word '{word_id}' to category '{category_id}': {e}"
        )
        raise DatabaseError(
            f"Failed to link word '{word_id}' to category '{category_id}': {e}"
        ) from e


def unlink_word_from_category(db, word_id: str, category_id: str) -> None:
    """Deletes the link document between a word and a category."""
    link_id = f"{word_id}_{category_id}"
    logger.info(
        f"DAL: Unlinking word {word_id} from category {category_id} with link_id {link_id}."
    )
    try:
        db.collection("word_categories").document(link_id).delete()
    except Exception as e:
        logger.error(
            f"DAL: Failed to unlink word '{word_id}' from category '{category_id}': {e}"
        )
        raise DatabaseError(
            f"Failed to unlink word '{word_id}' from category '{category_id}': {e}"
        ) from e


def check_link_exists(db, word_id: str, category_id: str) -> bool:
    """Checks if a link between a word and category exists."""
    link_id = f"{word_id}_{category_id}"
    logger.info(f"DAL: Checking if link exists for link_id {link_id}.")
    try:
        link_ref = db.collection("word_categories").document(link_id)
        return link_ref.get().exists
    except Exception as e:
        logger.error(
            f"DAL: Failed to check link for word '{word_id}' and category '{category_id}': {e}"
        )
        raise DatabaseError(
            f"Failed to check link for word '{word_id}' and category '{category_id}': {e}"
        ) from e


def get_word_ids_by_category_id(db, category_id: str) -> List[str]:
    """Retrieves all word_ids linked to a specific category_id."""
    logger.info(f"DAL: Getting word_ids for category_id {category_id}.")
    try:
        word_ids = []
        query = db.collection("word_categories").where("category_id", "==", category_id)
        docs = query.stream()
        for doc in docs:
            word_ids.append(doc.to_dict()["word_id"])
        logger.info(
            f"DAL: Found {len(word_ids)} words linked to category {category_id}."
        )
        return word_ids
    except Exception as e:
        logger.error(f"DAL: Failed to get words for category '{category_id}': {e}")
        raise DatabaseError(
            f"Failed to get words for category '{category_id}': {e}"
        ) from e
