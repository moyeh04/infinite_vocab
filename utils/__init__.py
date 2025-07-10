# Utils package - Utilities, exceptions, and helper functions


from .exceptions import (
    AdminServiceError,
    ApplicationError,
    CategoryServiceError,
    DatabaseError,
    DuplicateEntryError,
    ForbiddenError,
    NotFoundError,
    SearchServiceError,
    UserServiceError,
    ValidationError,
    WordServiceError,
)
from .helpers import generate_random_code
from .logging import setup_logging
from .response_helpers import camelized_response, decamelized_request, error_response

__all__ = [
    # Exceptions
    "AdminServiceError",
    "ApplicationError",
    "DatabaseError",
    "DuplicateEntryError",
    "ForbiddenError",
    "NotFoundError",
    "ValidationError",
    "WordServiceError",
    "CategoryServiceError",
    "SearchServiceError",
    "UserServiceError",
    # Helpers
    "generate_random_code",
    "camelized_response",
    "decamelized_request",
    "error_response",
    # Loggers
    "setup_logging",
]
