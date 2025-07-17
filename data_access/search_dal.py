"""Search Data Access Layer - For text-based search queries"""

import logging
from typing import List

from firebase_admin import firestore

from utils import DatabaseError

logger = logging.getLogger("infinite_vocab_app")


def search_words_by_name(db, user_id: str, query: str) -> List:
    """
    Searches for words where word_text_search starts with the query string (case-insensitive).

    Uses the dedicated word_text_search field for efficient case-insensitive searching
    while preserving the original capitalization in word_text for display.
    """
    logger.info(f"DAL: Searching words for user {user_id} with query '{query}'.")
    try:
        query_lower = query.lower()

        # Use the word_text_search field for efficient case-insensitive searching
        query_ref = (
            db.collection("words")
            .where(filter=firestore.FieldFilter("user_id", "==", user_id))
            .order_by("word_text_search")
            .where(filter=firestore.FieldFilter("word_text_search", ">=", query_lower))
            .where(
                filter=firestore.FieldFilter(
                    "word_text_search", "<=", query_lower + "\uf8ff"
                )
            )
        )

        results = list(query_ref.stream())

        logger.info(
            f"DAL: Word search for user {user_id} found {len(results)} results."
        )
        return results
    except Exception as e:
        logger.error(
            f"DAL: Database error while searching words for user {user_id}, query '{query}': {e}"
        )
        raise DatabaseError(
            f"Database error while searching words for query: '{query}'"
        ) from e


def search_categories_by_name(db, user_id: str, query: str) -> List:
    """
    Searches for categories where category_name_search starts with the query string (case-insensitive).

    Uses the dedicated category_name_search field for efficient case-insensitive searching
    while preserving the original capitalization in category_name for display.
    """
    logger.info(f"DAL: Searching categories for user {user_id} with query '{query}'.")
    try:
        query_lower = query.lower()

        # Use the category_name_search field for efficient case-insensitive searching
        query_ref = (
            db.collection("categories")
            .where(filter=firestore.FieldFilter("user_id", "==", user_id))
            .order_by("category_name_search")
            .where(
                filter=firestore.FieldFilter("category_name_search", ">=", query_lower)
            )
            .where(
                filter=firestore.FieldFilter(
                    "category_name_search", "<=", query_lower + "\uf8ff"
                )
            )
        )

        results = list(query_ref.stream())

        logger.info(
            f"DAL: Category search for user {user_id} found {len(results)} results."
        )
        return results
    except Exception as e:
        logger.error(
            f"DAL: Database error while searching categories for user {user_id}, query '{query}': {e}"
        )
        raise DatabaseError(
            f"Database error while searching categories for query: '{query}'"
        ) from e
