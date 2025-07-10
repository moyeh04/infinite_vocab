"""Service layer for handling search operations."""

from google.cloud.firestore_v1.client import (
    Client,
)  # Good for type checking, but still YAGANI

from data_access import search_dal
from models.search_models import (
    CategorySearchResult,
    SearchResults,
    WordSearchResult,
)
from utils import DatabaseError, SearchServiceError


def find_words_and_categories(db: Client, user_id: str, query: str) -> SearchResults:
    """
    Finds words and categories matching a query and returns them in a structured model.
    """
    try:
        # 1. Concurrently call the DAL to search both collections
        word_docs = search_dal.search_words_by_name(db, user_id, query)
        category_docs = search_dal.search_categories_by_name(db, user_id, query)

        # 2. Convert raw Firestore documents into Pydantic models

        # This list comprehension is a concise way to build the model list.

        # It unpacks the document's data dictionary (**doc.to_dict())
        # and explicitly passes the document ID.
        word_results = [
            WordSearchResult(word_id=doc.id, **doc.to_dict()) for doc in word_docs
        ]

        category_results = [
            CategorySearchResult(category_id=doc.id, **doc.to_dict())
            for doc in category_docs
        ]

        # 3. Package the results into the main response model
        return SearchResults(words=word_results, categories=category_results)

    except DatabaseError as e:
        # 4. Wrap database errors in a service-specific exception
        raise SearchServiceError("A database error occurred during the search.") from e
