import os
import sys
import time

from flask import Flask, g, request
from flask_cors import CORS

from routes import (
    admin_bp,
    category_bp,
    search_bp,
    user_bp,
    word_category_bp,
    words_bp,
)
from utils import log_response, setup_logging

# Initialize logging FIRST
logger = setup_logging()
logger.info("APP: Logging system initialized")

# Import config AFTER logging is set up
from config import firebase_init  # noqa: F401 E402

# Log system information
logger.info(f"APP: Python version: {sys.version}")
logger.info(f"APP: Running on platform: {sys.platform}")
logger.info(f"APP: Current working directory: {os.getcwd()}")

# Initialize Flask application
app = Flask(__name__)
logger.info("APP: Flask application instance created")

# Enable CORS with auth header support
CORS(
    app,
    origins=["http://localhost:5500", "http://localhost:3000", "http://127.0.0.1:5500"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    supports_credentials=True,
)
logger.info("APP: CORS enabled for all origins with preflight support")

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
def setup_request_timing():
    """Set up request timing for response logging."""
    g.request_start_time = time.time()


@app.after_request
def log_response_info(response):
    """Log details about outgoing responses."""
    return log_response(logger, request, response, g.request_start_time)


logger.info("APP: Application starting up, blueprints registered.")


@app.route("/")
def root_info():
    """Root endpoint for health check."""
    from flask import jsonify

    return jsonify(
        {
            "message": "Welcome to the Infinite Vocabulary API!",
            "version": "v1.0",
            "status": "healthy",
        }
    ), 200


if __name__ == "__main__":
    logger.info("APP: Starting Flask development server")

    # Set debug=True to enable Flask's debug mode
    app.run(debug=True, port=5000)
