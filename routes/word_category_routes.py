"""
Routes for managing the relationship between words and categories.
"""

import logging

from flask import Blueprint, g, jsonify, request

from middleware import firebase_token_required
from services import word_category_service as wcs
from utils import DuplicateEntryError, NotFoundError, WordServiceError

logger = logging.getLogger("infinite_vocab_app")
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
    logger.info(f"ROUTE: Getting words for category {category_id} for user {g.user_id}")
    try:
        words = wcs.get_words_for_category(g.db, g.user_id, category_id)
        return jsonify(words), 200
    except NotFoundError as e:
        logger.warning(
            f"ROUTE: Not found error for user {g.user_id} getting words for category {category_id}: {e}"
        )
        return jsonify({"error": str(e)}), 404

    except WordServiceError as e:
        logger.error(
            f"ROUTE: Service error for user {g.user_id} getting words for category {category_id}: {e}"
        )
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error getting words for category {category_id}: {e}",
            exc_info=True,
        )
        return jsonify({"error": "An unexpected error occurred."}), 500


@word_category_bp.route("/<category_id>/words", methods=["POST"])
def add_word_to_category_route(category_id: str):
    """Link an existing word to a category."""
    logger.info(f"ROUTE: Linking word to category {category_id} for user {g.user_id}")

    try:
        data = request.get_json()
        if not data or not data.get("wordId"):
            logger.warning(f"ROUTE: Missing 'wordId' in request for user {g.user_id}")
            return jsonify({"error": "Missing 'wordId' in request body."}), 400

        word_id = data.get("wordId")
        result = wcs.add_word_to_category(g.db, g.user_id, category_id, word_id)
        logger.info(
            f"ROUTE: Successfully linked word {word_id} to category {category_id} for user {g.user_id}"
        )
        return jsonify(result), 200
    except (NotFoundError, DuplicateEntryError) as e:
        logger.warning(
            f"ROUTE: Client error linking word to category {category_id} for user {g.user_id}: {e}"
        )
        return jsonify({"error": str(e)}), 400
    except WordServiceError as e:
        logger.error(
            f"ROUTE: Service error linking word to category {category_id} for user {g.user_id}: {e}"
        )
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error linking word to category {category_id} for user {g.user_id}: {e}",
            exc_info=True,
        )
        return jsonify({"error": "An unexpected error occurred."}), 500


@word_category_bp.route("/<category_id>/words/<word_id>", methods=["DELETE"])
def remove_word_from_category_route(category_id: str, word_id: str):
    """Unlink a word from a category."""
    logger.info(
        f"ROUTE: Unlinking word {word_id} from category {category_id} for user {g.user_id}"
    )
    try:
        result = wcs.remove_word_from_category(g.db, g.user_id, category_id, word_id)
        logger.info(
            f"ROUTE: Successfully unlinked word {word_id} from category {category_id} for user {g.user_id}"
        )
        return jsonify(result), 200
    except NotFoundError as e:
        logger.warning(
            f"ROUTE: Not found error unlinking word {word_id} from category {category_id} for user {g.user_id}: {e}"
        )
        return jsonify({"error": str(e)}), 404
    except WordServiceError as e:
        logger.error(
            f"ROUTE: Service error unlinking word {word_id} from category {category_id} for user {g.user_id}: {e}"
        )
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error unlinking word {word_id} from category {category_id} for user {g.user_id}: {e}",
            exc_info=True,
        )
        return jsonify({"error": "An unexpected error occurred."}), 500
