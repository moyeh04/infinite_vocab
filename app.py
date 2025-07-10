import logging

from flask import Flask

from config import firebase_init  # noqa: F401
from routes import (
    admin_bp,
    category_bp,
    search_bp,
    user_bp,
    word_category_bp,
    words_bp,
)
from utils import camelized_response, setup_logging

# Initialize logging
setup_logging()
logger = logging.getLogger("infinite_vocab_app")

app = Flask(__name__)

# Register all blueprints
app.register_blueprint(admin_bp)
app.register_blueprint(user_bp)
app.register_blueprint(words_bp)
app.register_blueprint(category_bp)
app.register_blueprint(word_category_bp)
app.register_blueprint(search_bp)


logger.info("Application starting up, blueprints registered.")


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
    logger.info("Starting Flask development server.")
    app.run(debug=True, port=5000)
