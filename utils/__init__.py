# Utils package - Utilities, exceptions, and helper functions

from .exceptions import (
    ApplicationError,
    CategoryServiceError,
    DatabaseError,
    DuplicateEntryError,
    ForbiddenError,
    NotFoundError,
    SearchServiceError,
    ValidationError,
    WordServiceError,
)
from .helpers import generate_random_code
from .response_helpers import (
    camelized_response,
    decamelized_request,
    error_response,
)

__all__ = [
    "ApplicationError",
    "DatabaseError",
    "ValidationError",
    "DuplicateEntryError",
    "NotFoundError",
    "ForbiddenError",
    "WordServiceError",
    "CategoryServiceError",
    "camelized_response",
    "decamelized_request",
    "error_response",
    "generate_random_code",
    "SearchServiceError",
]
