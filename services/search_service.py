"""Service layer for handling search operations."""

import logging

from google.cloud.firestore_v1.client import Client

from data_access import search_dal
from models import (
    CategorySearchResult,
    SearchResults,
    WordSearchResult,
)
from utils import DatabaseError, SearchServiceError

logger = logging.getLogger("infinite_vocab_app")


def find_words_and_categories(db: Client, user_id: str, query: str) -> SearchResults:
    """
    Finds words and categories matching a query and returns them in a structured model.
    """
    logger.info(
        f"SERVICE: find_words_and_categories invoked for user '{user_id}' with query '{query}'."
    )
    try:
        word_docs = search_dal.search_words_by_name(db, user_id, query)
        category_docs = search_dal.search_categories_by_name(db, user_id, query)
        logger.info(
            f"SERVICE: DAL found {len(word_docs)} words and {len(category_docs)} categories."
        )

        word_results = [
            WordSearchResult.model_validate(doc.to_dict() | {"word_id": doc.id})
            for doc in word_docs
        ]
        category_results = [
            CategorySearchResult.model_validate(doc.to_dict() | {"category_id": doc.id})
            for doc in category_docs
        ]

        return SearchResults(words=word_results, categories=category_results)

    except DatabaseError as e:
        logger.error(f"SERVICE: DatabaseError during search for user '{user_id}': {e}")
        raise SearchServiceError("A database error occurred during the search.") from e
