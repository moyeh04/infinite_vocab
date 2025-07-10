"""Logging configuration for the application."""

import logging
import sys


def setup_logging():
    """Configure application-wide logging."""
    # Using a specific name allows us to get this logger instance elsewhere.
    logger = logging.getLogger("infinite_vocab_app")
    logger.setLevel(logging.INFO)

    # Prevent adding multiple handlers if this function is called more than once.
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)

        formatter = logging.Formatter(
            "%(asctime)s - [%(name)s] - [%(levelname)s] - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
