# Utils package - Utilities, exceptions, and helper functions

from .exceptions import (
    ApplicationError,
    DatabaseError,
    ValidationError,
    DuplicateEntryError,
    NotFoundError,
    ForbiddenError,
    WordServiceError,
    CategoryServiceError,
)
from .response_helpers import (
    camelized_response,
    decamelized_request,
    error_response,
)
from .helpers import generate_random_code

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
]
