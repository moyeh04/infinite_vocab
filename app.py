import os
import sys
import time

from flask import Flask, g, request

from config import firebase_init  # noqa: F401
from routes import (
    admin_bp,
    category_bp,
    search_bp,
    user_bp,
    word_category_bp,
    words_bp,
)
from utils import camelized_response
from utils.logging import log_request, log_response, setup_logging

# Initialize logging
logger = setup_logging()
logger.info("APP: Logging system initialized")

# Log system information
logger.info(f"APP: Python version: {sys.version}")
logger.info(f"APP: Running on platform: {sys.platform}")
logger.info(f"APP: Current working directory: {os.getcwd()}")

# Initialize Flask application
app = Flask(__name__)
logger.info("APP: Flask application instance created")

# Register all blueprints
blueprint_count = 0

# Register all blueprints with logging
for bp_name, blueprint in [
    ("admin", admin_bp),
    ("user", user_bp),
    ("words", words_bp),
    ("category", category_bp),
    ("word_category", word_category_bp),
    ("search", search_bp),
]:
    app.register_blueprint(blueprint)
    blueprint_count += 1
    logger.debug(
        f"APP: Registered blueprint '{bp_name}' with prefix '{blueprint.url_prefix}'"
    )

logger.info(f"APP: Successfully registered {blueprint_count} blueprints")


# Request/response logging middleware
@app.before_request
def log_request_info():
    """Log details about incoming requests."""
    g.request_start_time = time.time()
    log_request(logger, request)


@app.after_request
def log_response_info(response):
    """Log details about outgoing responses."""
    return log_response(logger, request, response, g.request_start_time)


logger.info("APP: Application starting up, blueprints registered.")


@app.route("/")
def root_info():
    """Root endpoint for health check."""
    return camelized_response(
        {
            "message": "Welcome to the Infinite Vocabulary API!",
            "version": "v1.0",
            "status": "healthy",
        },
        200,
    )


if __name__ == "__main__":
    # Test logging at different levels
    logger.debug(
        "APP: This is a DEBUG message - visible only when DEBUG level is enabled"
    )
    logger.info("APP: Starting Flask development server.")
    logger.warning("APP: This is a WARNING message - should always be visible")
    logger.error("APP: This is an ERROR message - should always be visible")

    # Set debug=True to enable Flask's debug mode
    app.run(debug=True, port=5000)
