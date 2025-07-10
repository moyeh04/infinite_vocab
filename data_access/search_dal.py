"""Search Data Access Layer - For text-based search queries"""

import logging
from typing import List

from utils import DatabaseError

logger = logging.getLogger("infinite_vocab_app")


def search_words_by_name(db, user_id: str, query: str) -> List:
    """Searches for words where word_text starts with the query string."""
    logger.info(f"DAL: Searching words for user {user_id} with query '{query}'.")
    try:
        query_text = query.lower()

        query_ref = (
            db.collection("words")
            .where("user_id", "==", user_id)
            .order_by("word_text")
            .where("word_text", ">=", query_text)
            .where("word_text", "<=", query_text + "\uf8ff")
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
    """Searches for categories where category_name starts with the query string."""
    logger.info(f"DAL: Searching categories for user {user_id} with query '{query}'.")
    try:
        query_text = query.lower()
        query_ref = (
            db.collection("categories")
            .where("user_id", "==", user_id)
            .order_by("category_name")
            .where("category_name", ">=", query_text)
            .where("category_name", "<=", query_text + "\uf8ff")
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
