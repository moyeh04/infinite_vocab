class ApplicationError(Exception):
    """Base class for all custom application exceptions."""

    def __init__(
        self,
        message="An application error occurred.",
        status_code=500,
        context=None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.context = context if context is not None else {}


class DatabaseError(ApplicationError):
    """Raised for general database interaction errors."""

    def __init__(self, message="A database error occurred.", context=None):
        super().__init__(message, context=context)


class DuplicateEntryError(ApplicationError):
    """Raised when trying to create an entry that already exists."""

    def __init__(
        self,
        message="This entry already exists.",
        conflicting_id=None,
        context=None,
    ):
        super().__init__(message, status_code=409, context=context)
        self.conflicting_id = conflicting_id


class NotFoundError(ApplicationError):
    """Raised when a requested resource is not found."""

    def __init__(self, message="Resource not found.", context=None):
        super().__init__(message, status_code=404, context=context)


class ForbiddenError(ApplicationError):
    """Raised when a user is not authorized to perform an action on a resource."""

    def __init__(
        self,
        message="You are not authorized to perform this action.",
        context=None,
    ):
        super().__init__(message, status_code=403, context=context)


class ValidationError(ApplicationError):
    """Raised for input validation errors."""

    def __init__(
        self, message="Invalid input provided.", field_errors=None, context=None
    ):
        super().__init__(message, status_code=400, context=context)
        self.field_errors = field_errors if field_errors is not None else {}


class WordServiceError(ApplicationError):
    """Base exception for errors specific to the WordService."""

    def __init__(self, message="A word service operation failed.", context=None):
        super().__init__(message, status_code=500, context=context)


class CategoryServiceError(ApplicationError):
    """Base exception for errors specific to the CategoryService."""

    def __init__(self, message="A category service operation failed.", context=None):
        super().__init__(message, status_code=500, context=context)


class SearchServiceError(ApplicationError):
    """Base exception for errors specific to the SearchService."""

    def __init__(self, message="A search service operation failed.", context=None):
        super().__init__(message, status_code=500, context=context)


class UserServiceError(ApplicationError):
    """Base exception for errors specific to the UserService."""

    def __init__(self, message="A user service operation failed.", context=None):
        super().__init__(message, status_code=500, context=context)
