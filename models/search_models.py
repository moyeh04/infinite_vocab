"""Pydantic models for representing search results."""

from typing import List

from pydantic import BaseModel, Field


class WordSearchResult(BaseModel):
    """A lightweight model for a word in search results."""

    word_id: str = Field(..., alias="wordId")
    word_text: str = Field(..., alias="wordText")

    class Config:
        populate_by_name = True


class CategorySearchResult(BaseModel):
    """A lightweight model for a category in search results."""

    category_id: str = Field(..., alias="categoryId")

    category_name: str = Field(..., alias="categoryName")

    class Config:
        populate_by_name = True


class SearchResults(BaseModel):
    """The main response model for the search endpoint."""

    words: List[WordSearchResult]
    categories: List[CategorySearchResult]

    class Config:
        # This ensures that when we call .model_dump(), it uses the aliases
        # we defined (e.g., 'wordId' instead of 'word_id').
        populate_by_name = True
