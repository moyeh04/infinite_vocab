"""Logging configuration for the application."""

import logging
import os
import sys
import time
from functools import wraps
from typing import Callable, Optional


def setup_logging(log_level: Optional[str] = None):
    """
    Configure application-wide logging.

    Args:
        log_level: Optional log level override (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                  If not provided, uses INFO by default or DEBUG if LOG_LEVEL env var is set

    Returns:
        Configured logger instance
    """
    # Using a specific name allows us to get this logger instance elsewhere.
    logger = logging.getLogger("infinite_vocab_app")

    # Determine log level from argument, environment variable, or default to INFO
    if log_level:
        level = getattr(logging, log_level.upper())
    elif os.environ.get("LOG_LEVEL"):
        level = getattr(logging, os.environ.get("LOG_LEVEL").upper())
    else:
        level = logging.INFO

    logger.setLevel(level)

    # Prevent adding multiple handlers if this function is called more than once.
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)

        formatter = logging.Formatter(
            "%(asctime)s - [%(name)s] - [%(levelname)s] - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Log the configured level
        logger.info(f"APP: Logging initialized at {logging.getLevelName(level)} level")

    return logger


def log_request(logger, request):
    """
    Log details about an incoming request.

    Args:
        logger: Logger instance
        request: Flask request object
    """
    user_id = getattr(request, "user_id", None) or "anonymous"
    logger.info(f"REQUEST: {request.method} {request.path} - User: {user_id}")

    # Log request body at DEBUG level (sanitized for sensitive data)
    if logger.isEnabledFor(logging.DEBUG) and request.is_json:
        try:
            # Create a copy of the json to avoid modifying the original
            # Use silent=True to avoid raising exceptions for invalid JSON
            sanitized_data = request.get_json(silent=True) or {}
            if isinstance(sanitized_data, dict):
                # Sanitize sensitive fields if present
                for field in ["password", "token", "secret", "key"]:
                    if field in sanitized_data:
                        sanitized_data[field] = "[REDACTED]"

                # Truncate large request bodies to avoid flooding logs
                request_str = str(sanitized_data)
                if len(request_str) > 1000:
                    request_str = request_str[:1000] + "... [truncated]"
                logger.debug(f"REQUEST BODY: {request_str}")
        except Exception:
            # Don't let request logging errors affect the request processing
            pass


def log_response(logger, request, response, start_time=None):
    """
    Log details about an outgoing response.

    Args:
        logger: Logger instance
        request: Flask request object
        response: Flask response object
        start_time: Optional start time for calculating duration

    Returns:
        The original response object (for chaining)
    """
    duration = ""
    if start_time:
        duration = f" - Duration: {(time.time() - start_time) * 1000:.0f}ms"

    logger.info(f"RESPONSE: {request.path} - Status: {response.status_code}{duration}")

    # Log response body at DEBUG level for JSON responses
    if logger.isEnabledFor(logging.DEBUG) and response.is_json:
        try:
            # Get a copy of the response data without modifying the original
            response_data = response.get_json(silent=True)
            if response_data:
                # Truncate large responses to avoid flooding logs
                response_str = str(response_data)
                if len(response_str) > 1000:
                    response_str = response_str[:1000] + "... [truncated]"
                logger.debug(f"RESPONSE BODY: {response_str}")
        except Exception:
            # Don't let response logging errors affect the response
            pass

    return response


def timed_execution(logger, label: str) -> Callable:
    """
    Decorator for timing function execution and logging the duration.

    Args:
        logger: Logger instance
        label: Label to identify the timed operation

    Returns:
        Decorator function
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = (time.time() - start_time) * 1000
            logger.debug(f"TIMING: {label} completed in {duration:.0f}ms")
            return result

        return wrapper

    return decorator
