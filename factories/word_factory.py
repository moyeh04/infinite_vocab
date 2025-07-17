"""Word Factory - Business Logic for Word objects"""

import logging
from typing import Dict, Tuple

from models import Word, Description, Example
from schemas import (
    WordCreateSchema,
    WordUpdateSchema,
    DescriptionCreateSchema,
    DescriptionUpdateSchema,
    ExampleCreateSchema,
    ExampleUpdateSchema,
)

logger = logging.getLogger("infinite_vocab_app")


class WordFactory:
    """Factory for creating Word objects with business rules and validation"""

    @staticmethod
    def create_from_schema(schema: WordCreateSchema, user_id: str) -> Word:
        """
        Create Word from validated schema with business rules applied.

        Business rules applied:
        - New words start with 0 stars
        - Word text preserves user's original capitalization
        """
        logger.info(f"FACTORY: Creating new word model from schema for user: {user_id}")

        return Word(
            word_text=schema.word_text,  # Preserve original capitalization
            word_text_search=schema.word_text.lower(),  # Lowercase version for searching
            word_stars=0,  # Business rule: new words start with 0 stars
            user_id=user_id,
        )

    @staticmethod
    def create_description_from_schema(
        schema: DescriptionCreateSchema, user_id: str, is_initial: bool = False
    ) -> Description:
        """Create Description model from validated schema"""
        logger.info(
            f"FACTORY: Creating description model from schema for user: {user_id}"
        )

        return Description(
            description_text=schema.description_text,
            is_initial=is_initial,
            user_id=user_id,
        )

    @staticmethod
    def create_example_from_schema(
        schema: ExampleCreateSchema, user_id: str, is_initial: bool = False
    ) -> Example:
        """Create Example model from validated schema"""
        logger.info(f"FACTORY: Creating example model from schema for user: {user_id}")

        return Example(
            example_text=schema.example_text,
            is_initial=is_initial,
            user_id=user_id,
        )

    @staticmethod
    def create_word_update_dict(schema: WordUpdateSchema) -> dict:
        """Create update dictionary for DAL operations from validated schema"""
        updates = {
            "word_text": schema.word_text,  # Preserve original capitalization
            "word_text_search": schema.word_text.lower(),  # Lowercase version for searching
        }

        logger.info(
            f"FACTORY: Created word update dictionary with keys: {list(updates.keys())}"
        )
        return updates

    @staticmethod
    def create_description_update_dict(schema: DescriptionUpdateSchema) -> dict:
        """Create update dictionary for description DAL operations"""
        updates = {
            "description_text": schema.description_text,
        }

        logger.info(f"FACTORY: Created description update dictionary")
        return updates

    @staticmethod
    def create_example_update_dict(schema: ExampleUpdateSchema) -> dict:
        """Create update dictionary for example DAL operations"""
        updates = {
            "example_text": schema.example_text,
        }

        logger.info(f"FACTORY: Created example update dictionary")
        return updates

    @staticmethod
    def validate_star_milestones(star_count: int) -> Dict[str, bool]:
        """
        Business rule: Check if star count triggers description/example prompts.

        Milestone rules:
        - Description prompts at: 5, 10, 15, 20 stars
        - Example prompts at: 10, 20, 30, 40 stars

        Returns:
            dict: {"prompt_for_description": bool, "prompt_for_example": bool}
        """
        description_milestones = [5, 10, 15, 20]
        example_milestones = [10, 20, 30, 40]

        prompt_for_description = star_count in description_milestones
        prompt_for_example = star_count in example_milestones

        if prompt_for_description or prompt_for_example:
            logger.info(
                f"FACTORY: Star milestone reached at {star_count} stars - "
                f"description: {prompt_for_description}, example: {prompt_for_example}"
            )

        return {
            "prompt_for_description": prompt_for_description,
            "prompt_for_example": prompt_for_example,
        }
