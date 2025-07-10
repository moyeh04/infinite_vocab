"""
Routes for managing the relationship between words and categories.
"""

from flask import Blueprint, g, jsonify, request

from middleware import firebase_token_required
from services import word_category_service as wcs
from utils import DuplicateEntryError, NotFoundError, WordServiceError

word_category_bp = Blueprint(
    "word_category_api", __name__, url_prefix="/api/v1/categories"
)


@word_category_bp.before_request
def authentication_before_request():
    """Apply Firebase token authentication to all routes in this blueprint."""
    return firebase_token_required()


@word_category_bp.route("/<category_id>/words", methods=["GET"])
def get_words_in_category_route(category_id: str):
    """Get all words linked to a specific category."""
    try:
        words = wcs.get_words_for_category(g.db, g.user_id, category_id)
        # Note: We use jsonify directly because the service returns a list of dicts.
        return jsonify(words), 200
    except NotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except WordServiceError as e:
        return jsonify({"error": str(e)}), 500
    except Exception:
        return jsonify({"error": "An unexpected error occurred."}), 500


@word_category_bp.route("/<category_id>/words", methods=["POST"])
def add_word_to_category_route(category_id: str):
    """Link an existing word to a category."""
    try:
        data = request.get_json()
        if not data or not data.get("wordId"):
            return jsonify({"error": "Missing 'wordId' in request body."}), 400

        word_id = data.get("wordId")
        result = wcs.add_word_to_category(g.db, g.user_id, category_id, word_id)
        return jsonify(result), 200
    except (NotFoundError, DuplicateEntryError) as e:
        # Business logic errors that are the client's fault
        return jsonify({"error": str(e)}), 400
    except WordServiceError as e:
        return jsonify({"error": str(e)}), 500
    except Exception:
        return jsonify({"error": "An unexpected error occurred."}), 500


@word_category_bp.route("/<category_id>/words/<word_id>", methods=["DELETE"])
def remove_word_from_category_route(category_id: str, word_id: str):
    """Unlink a word from a category."""
    try:
        result = wcs.remove_word_from_category(g.db, g.user_id, category_id, word_id)
        return jsonify(result), 200
    except NotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except WordServiceError as e:
        return jsonify({"error": str(e)}), 500
    except Exception:
        return jsonify({"error": "An unexpected error occurred."}), 500
