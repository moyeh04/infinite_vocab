"""
Word services package - Clean architecture with proper separation of concerns.

This package splits the monolithic word service into focused domain services:
- word_service.py: Core word CRUD operations
- description_service.py: Description CRUD operations
- example_service.py: Example CRUD operations
- star_service.py: Star and milestone logic

Each service follows the same clean patterns as category_service.py.
"""

# Import all public functions to maintain backward compatibility
# Routes can still use: from services import word as ws

# Core word operations
from .word_service import (
    create_word_for_user,
    get_word_details_for_user,
    update_word_for_user,
    delete_word_for_user,
    list_words_for_user,
    check_word_exists,
)

# Description operations
from .description_service import (
    add_description_for_user,
    update_description_for_user,
    delete_description_for_user,
)

# Example operations
from .example_service import (
    add_example_for_user,
    update_example_for_user,
    delete_example_for_user,
)

# Star operations
from .star_service import star_word_for_user

# Maintain backward compatibility - all existing imports work unchanged
__all__ = [
    # Core word operations
    "create_word_for_user",
    "get_word_details_for_user",
    "update_word_for_user",
    "delete_word_for_user",
    "list_words_for_user",
    "check_word_exists",
    # Description operations
    "add_description_for_user",
    "update_description_for_user",
    "delete_description_for_user",
    # Example operations
    "add_example_for_user",
    "update_example_for_user",
    "delete_example_for_user",
    # Star operations
    "star_word_for_user",
]
