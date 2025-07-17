from pydantic import BaseModel, Field
from typing import Optional


class WordCreateSchema(BaseModel):
    """Schema for validating word creation requests"""

    word_text: str = Field(
        alias="wordText",
        min_length=1,
        max_length=100,
        strip_whitespace=True,
        description="The word text to be added",
    )

    description_text: str = Field(
        alias="descriptionText",
        min_length=1,
        max_length=500,
        strip_whitespace=True,
        description="Initial description for the word",
    )

    example_text: str = Field(
        alias="exampleText",
        min_length=1,
        max_length=500,
        strip_whitespace=True,
        description="Initial example for the word",
    )

    class Config:
        # Allow both snake_case and camelCase field names
        populate_by_name = True
        # Example for API documentation
        json_schema_extra = {
            "title": "Word Creation Request",
            "description": "Schema for creating a new vocabulary word with initial description and example",
            "example": {
                "wordText": "explain",
                "descriptionText": "To make something clear or easy to understand",
                "exampleText": "Can you explain this concept to me?",
            },
        }


class WordUpdateSchema(BaseModel):
    """Schema for validating word text update requests"""

    word_text: str = Field(
        alias="wordText",
        min_length=1,
        max_length=100,
        strip_whitespace=True,
        description="Updated word text",
    )

    class Config:
        # Allow both snake_case and camelCase field names
        populate_by_name = True
        json_schema_extra = {
            "title": "Word Update Request",
            "description": "Schema for updating word text",
            "example": {"wordText": "clarify"},
        }


class WordExistenceCheckSchema(BaseModel):
    """Schema for validating word existence check requests"""

    word_text: str = Field(
        alias="wordText",
        min_length=1,
        max_length=100,
        strip_whitespace=True,
        description="Word text to check for existence",
    )

    class Config:
        # Allow both snake_case and camelCase field names
        populate_by_name = True
        json_schema_extra = {
            "title": "Word Existence Check Request",
            "description": "Schema for checking if a word already exists",
            "example": {"wordText": "explain"},
        }


class DescriptionCreateSchema(BaseModel):
    """Schema for validating description creation requests"""

    description_text: str = Field(
        alias="descriptionText",
        min_length=1,
        max_length=500,
        strip_whitespace=True,
        description="Description text for the word",
    )

    class Config:
        # Allow both snake_case and camelCase field names
        populate_by_name = True
        json_schema_extra = {
            "title": "Description Creation Request",
            "description": "Schema for adding a new description to a word",
            "example": {
                "descriptionText": "To make something clear or easy to understand"
            },
        }


class DescriptionUpdateSchema(BaseModel):
    """Schema for validating description update requests"""

    description_text: str = Field(
        alias="descriptionText",
        min_length=1,
        max_length=500,
        strip_whitespace=True,
        description="Updated description text",
    )

    class Config:
        # Allow both snake_case and camelCase field names
        populate_by_name = True
        json_schema_extra = {
            "title": "Description Update Request",
            "description": "Schema for updating an existing description",
            "example": {
                "descriptionText": "To clarify or make something easier to understand"
            },
        }


class ExampleCreateSchema(BaseModel):
    """Schema for validating example creation requests"""

    example_text: str = Field(
        alias="exampleText",
        min_length=1,
        max_length=500,
        strip_whitespace=True,
        description="Example text for the word",
    )

    class Config:
        # Allow both snake_case and camelCase field names
        populate_by_name = True
        json_schema_extra = {
            "title": "Example Creation Request",
            "description": "Schema for adding a new example to a word",
            "example": {"exampleText": "Can you explain this concept to me?"},
        }


class ExampleUpdateSchema(BaseModel):
    """Schema for validating example update requests"""

    example_text: str = Field(
        alias="exampleText",
        min_length=1,
        max_length=500,
        strip_whitespace=True,
        description="Updated example text",
    )

    class Config:
        # Allow both snake_case and camelCase field names
        populate_by_name = True
        json_schema_extra = {
            "title": "Example Update Request",
            "description": "Schema for updating an existing example",
            "example": {"exampleText": "Please explain this topic in detail"},
        }
