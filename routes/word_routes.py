from flask import Blueprint, g, jsonify, request

from middleware.firebase_auth_check import firebase_token_required
from services.word_service import (
    create_word_for_user,
    get_word_details_for_user,
    list_words_for_user,
    star_word_for_user,
)
from utils.exceptions import (
    # DatabaseError, It will rise as WordServiceError
    DuplicateEntryError,
    ForbiddenError,
    NotFoundError,
    WordServiceError,
)

words_bp = Blueprint("words_api", __name__, url_prefix="/api/v1/words")


@words_bp.before_request
def authenticate_before_request():
    return firebase_token_required()


@words_bp.route("/", methods=["POST"])
def create_word():
    request_data = request.get_json()
    if not request_data:
        return jsonify({"error": "Missing or invalid JSON request body"}), 400

    word = request_data.get("word")

    if not word or not word.strip():
        return jsonify({"error": "Missing or empty 'word' field in JSON body"}), 400

    word = word.strip()
    print(f"Input validation passed. Word to add: {word}")

    try:
        new_word_details = create_word_for_user(g.db, g.user_id, word)

        return jsonify(new_word_details), 201
    except DuplicateEntryError as e:
        print(f"ROUTE: Duplicate word - {str(e)}")
        # Use the attributes from the custom exception
        return jsonify(
            {
                "message": e.message,  # Or str(e)
                "existing_word_id": e.conflicting_id,
            }
        ), e.status_code  # Use status_code from exception (will be 409)
    except WordServiceError as e:
        print(f"ROUTE: WordServiceError - {str(e)}")
        return jsonify({"error": e.message, "context": e.context}), e.status_code
    except Exception as e:
        print(f"ROUTE: Unexpected error in list_words for UID {g.user_id}: {str(e)}")
        return jsonify({"error": "An unexpected server error occurred."}), 500


@words_bp.route("/", methods=["GET"])
def list_words():
    print(f"ROUTE: Attempting to fetch words for UID: {g.user_id}")
    try:
        word_list_data = list_words_for_user(g.db, g.user_id)
        return jsonify(word_list_data), 200
    except WordServiceError as e:
        print(f"ROUTE: WordServiceError fetching words for UID {g.user_id}: {str(e)}")
        return jsonify({"error": e.message, "context": e.context}), e.status_code  # 500
    except Exception as e:
        print(f"ROUTE: Unexpected error fetching words for UID {g.user_id}: {str(e)}")
        return jsonify({"error": "An error occurred while fetching words."}), 500


@words_bp.route("/<word_id>", methods=["GET"])
def word_stats(word_id: str):
    print(
        f"ROUTE: Attempting to fetch word details for word_id: {word_id}, UID: {g.user_id}"
    )
    try:
        word_details = get_word_details_for_user(g.db, g.user_id, word_id)

        return jsonify(word_details), 200

    except NotFoundError as e:
        print(f"ROUTE: NotFoundError for word_id {word_id}, UID {g.user_id} - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code  # 404
    except WordServiceError as e:
        print(
            f"ROUTE: WordServiceError for word_id {word_id}, UID {g.user_id} - {str(e)}"
        )
        return jsonify({"error": e.message, "context": e.context}), e.status_code  # 500
    except Exception as e:
        print(
            f"ROUTE: Unexpected error in get_word_details_route for word_id {word_id}, UID {g.user_id}: {str(e)}"
        )
        return jsonify({"error": "An unexpected server error occurred."}), 500


@words_bp.route("/<word_id>/star", methods=["POST"])
def star_word(word_id):
    try:
        success_data = star_word_for_user(g.db, g.user_id, word_id)
        return jsonify(success_data), 200
    except NotFoundError as e:
        print(f"ROUTE: Word not found - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code  # 404
    except ForbiddenError as e:
        print(f"ROUTE: Forbidden to star word - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code  # 403
    except WordServiceError as e:
        print(f"ROUTE: WordServiceError - {str(e)}")
        return jsonify({"error": e.message, "context": e.context}), e.status_code  # 500
    except Exception as e:
        print(f"ROUTE: Unexpected error in star_word for word_id {word_id}: {str(e)}")
        return jsonify({"error": "An unexpected server error occurred."}), 500
