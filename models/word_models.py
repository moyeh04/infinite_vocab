"""Word domain models for responses and internal operations"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Description(BaseModel):
    """Description sub-entity for word descriptions"""

    description_id: Optional[str] = Field(alias="descriptionId", default=None)
    description_text: str = Field(alias="descriptionText")
    is_initial: bool = Field(alias="isInitial", default=False)
    user_id: str = Field(alias="userId")
    created_at: Optional[datetime] = Field(alias="createdAt", default=None)
    updated_at: Optional[datetime] = Field(alias="updatedAt", default=None)

    class Config:
        # Allow creating model from dicts with either snake_case or camelCase keys
        populate_by_name = True
        # Serialization rules - convert Python types to JSON-safe types
        json_encoders = {datetime: lambda dt: dt.isoformat()}


class Example(BaseModel):
    """Example sub-entity for word examples"""

    example_id: Optional[str] = Field(alias="exampleId", default=None)
    example_text: str = Field(alias="exampleText")
    is_initial: bool = Field(alias="isInitial", default=False)
    user_id: str = Field(alias="userId")
    created_at: Optional[datetime] = Field(alias="createdAt", default=None)
    updated_at: Optional[datetime] = Field(alias="updatedAt", default=None)

    class Config:
        # Allow creating model from dicts with either snake_case or camelCase keys
        populate_by_name = True
        # Serialization rules - convert Python types to JSON-safe types
        json_encoders = {datetime: lambda dt: dt.isoformat()}


class Word(BaseModel):
    """Main word entity for responses and internal operations"""

    word_id: Optional[str] = Field(alias="wordId", default=None)
    user_id: str = Field(alias="userId")
    word_text: str = Field(alias="wordText")
    word_text_search: str = Field(
        alias="wordTextSearch"
    )  # Lowercase version for searching
    word_stars: int = Field(alias="wordStars", default=0)
    created_at: Optional[datetime] = Field(alias="createdAt", default=None)
    updated_at: Optional[datetime] = Field(alias="updatedAt", default=None)
    descriptions: List[Description] = Field(default_factory=list)
    examples: List[Example] = Field(default_factory=list)

    class Config:
        # Allow creating model from dicts with either snake_case or camelCase keys
        populate_by_name = True
        # Serialization rules - convert Python types to JSON-safe types
        json_encoders = {datetime: lambda dt: dt.isoformat()}
