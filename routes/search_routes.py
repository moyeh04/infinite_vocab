"""Routes for handling global search functionality."""

import logging

from flask import Blueprint, g, jsonify, request

from middleware import firebase_token_required
from services import search_service
from utils import SearchServiceError

logger = logging.getLogger("infinite_vocab_app")
search_bp = Blueprint("search", __name__, url_prefix="/api/v1/search")


@search_bp.before_request
def authentication_before_request():
    """Apply Firebase token authentication to all routes in this blueprint."""
    return firebase_token_required()


@search_bp.route("/", methods=["GET"])
def search_route():
    """
    Performs a prefix search across words and categories for the user.
    Expects a query parameter 'q'.
    """
    logger.info(f"ROUTE: search_route invoked for user_id: {g.user_id}")
    try:
        query = request.args.get("q", "").strip()
        if not query:
            logger.info("ROUTE: Empty search query received, returning empty result.")
            return jsonify({"words": [], "categories": []}), 200

        logger.info(f"ROUTE: Performing search for query: '{query}'")
        results_model = search_service.find_words_and_categories(
            db=g.db, user_id=g.user_id, query=query
        )
        return jsonify(results_model.model_dump(by_alias=True)), 200

    except SearchServiceError as e:
        logger.error(f"ROUTE: Service error during search for user {g.user_id}: {e}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error during search for user {g.user_id}: {e}",
            exc_info=True,
        )
        return jsonify({"error": "An unexpected server error occurred."}), 500
