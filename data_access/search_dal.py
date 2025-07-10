"""Search Data Access Layer - For text-based search queries"""

from typing import List

from utils import DatabaseError


def search_words_by_name(db, user_id: str, query: str) -> List:
    """Searches for words where word_text starts with the query string."""
    try:
        query_text = query.lower()
        # \uf8ff is a high-value Unicode character that acts as an effective upper bound
        # for all strings that start with the query_text, enabling a prefix search.
        query_ref = (
            db.collection("words")
            .where("user_id", "==", user_id)
            .order_by("word_text")
            .where("word_text", ">=", query_text)
            .where("word_text", "<=", query_text + "\uf8ff")
        )
        return list(query_ref.stream())
    except Exception as e:
        raise DatabaseError(
            f"Database error while searching words for query: '{query}'"
        ) from e


def search_categories_by_name(db, user_id: str, query: str) -> List:
    """Searches for categories where category_name starts with the query string."""

    try:
        query_text = query.lower()
        query_ref = (
            db.collection("categories")
            .where("user_id", "==", user_id)
            .order_by("category_name")
            .where("category_name", ">=", query_text)
            .where("category_name", "<=", query_text + "\uf8ff")
        )
        return list(query_ref.stream())
    except Exception as e:
        raise DatabaseError(
            f"Database error while searching categories for query: '{query}'"
        ) from e
