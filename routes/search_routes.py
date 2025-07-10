"""Routes for handling global search functionality."""

from flask import Blueprint, g, jsonify, request

from middleware import firebase_token_required
from services import search_service
from utils import SearchServiceError

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
    try:
        # 1. Get the search query from the request's query parameters
        query = request.args.get("q", "").strip()

        # If the query is empty, return an empty result immediately.
        if not query:
            return jsonify({"words": [], "categories": []}), 200

        # 2. Call the service layer to perform the search

        results_model = search_service.find_words_and_categories(
            db=g.db, user_id=g.user_id, query=query
        )

        # 3. Let Pydantic handle all the serialization and aliasing work

        return jsonify(results_model.model_dump(by_alias=True)), 200

    except SearchServiceError as e:
        # Known service-level errors (e.g., database issues)
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        # Catch any other unexpected errors

        print(f"SearchRoutes: Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected server error occurred."}), 500
