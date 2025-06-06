from flask import Blueprint, g, jsonify, request

from middleware.firebase_auth_check import firebase_token_required
from services import word_service as ws
from utils.exceptions import (
    # DatabaseError, # It will rise as WordServiceError
    DuplicateEntryError,
    ForbiddenError,
    NotFoundError,
    WordServiceError,
)

words_bp = Blueprint("words_api", __name__, url_prefix="/api/v1/words")


@words_bp.before_request
def authenticate_before_request():
    return firebase_token_required()


@words_bp.route("/check-existence", methods=["POST"])
def check_word_existence():
    request_data = request.get_json()
    if not request_data:
        return jsonify({"error": "Missing or invalid JSON request body"}), 400

    word_text = request_data.get("word")
    if not word_text or not word_text.strip():
        return jsonify({"error": "Missing or empty 'word' field in JSON body"}), 400
    word_text = word_text.strip()

    print(f"ROUTE: Checking existence for word '{word_text}' for UID {g.user_id}")
    try:
        existence_details = ws.check_word_exists(g.db, g.user_id, word_text)
        return jsonify(existence_details), 200
    except WordServiceError as e:
        print(
            f"ROUTE: WordServiceError during check_existence for word '{word_text}', UID {g.user_id}: {str(e)}"
        )
        return jsonify({"error": e.message, "context": e.context}), e.status_code
    except Exception as e:
        print(
            f"ROUTE: Unexpected error in check_existence for word '{word_text}', UID {g.user_id}: {str(e)}"
        )
        return jsonify(
            {"error": "An unexpected error occurred while checking word existence."}
        ), 500


@words_bp.route("/", methods=["POST"])
def create_word():
    request_data = request.get_json()
    if not request_data:
        return jsonify({"error": "Missing or invalid JSON request body"}), 400

    word = request_data.get("word")
    if not word or not word.strip():
        return jsonify({"error": "Missing or empty 'word' field in JSON body"}), 400
    word = word.strip()

    initial_description = request_data.get("description")
    if not initial_description or not initial_description.strip():
        return jsonify(
            {"error": "Missing or empty 'description' field in JSON body"}
        ), 400
    initial_description = initial_description.strip()

    initial_example = request_data.get("example")
    if not initial_example or not initial_example.strip():
        return jsonify({"error": "Missing or empty 'example' field in JSON body"}), 400
    initial_example = initial_example.strip()

    print(
        f"Input validation passed. Word to add: {word}, Description: {initial_description}, Example: {initial_example}"
    )

    try:
        new_word_details = ws.create_word_for_user(
            g.db, g.user_id, word, initial_description, initial_example
        )

        return jsonify(new_word_details), 201
    except DuplicateEntryError as e:
        print(f"ROUTE: Duplicate word - {str(e)}")
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
        word_list_data = ws.list_words_for_user(g.db, g.user_id)
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
        word_details = ws.get_word_details_for_user(g.db, g.user_id, word_id)

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


@words_bp.route("/<word_id>", methods=["PATCH"])
def update_word(word_id: str):
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({"error": "Missing or invalid JSON request body"}), 400

        word_text = request_data.get("word")
        if not word_text or not word_text.strip():
            return jsonify({"error": "Missing or empty 'word' field in JSON body"}), 400
        word_text = word_text.strip()

        print(f"Input validation passed. Word to rename: {word_text}")
        success_data = ws.edit_word_for_user(g.db, g.user_id, word_id, word_text)
        return jsonify(success_data), 200
    except NotFoundError as e:
        print(f"ROUTE: Word not found - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code  # 404
    except ForbiddenError as e:
        print(f"ROUTE: Forbidden to edit word - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code  # 403
    except WordServiceError as e:
        print(f"ROUTE: WordServiceError - {str(e)}")
        return jsonify({"error": e.message, "context": e.context}), e.status_code  # 500
    except Exception as e:
        print(
            f"ROUTE: Unexpected error in edit_word_for_user for word_id {word_id}: {str(e)}"
        )
        return jsonify({"error": "An unexpected server error occurred."}), 500


@words_bp.route("/<word_id>", methods=["DELETE"])
def delete_word(word_id: str):
    """
    Delete a word associated with the current user.
    """
    try:
        print(f"[DELETE /{word_id}] User {g.user_id} - Deleting word...")
        success_data = ws.delete_word_for_user(g.db, g.user_id, word_id)
        print(f"[DELETE /{word_id}] User {g.user_id} - Successfully deleted word.")
        return jsonify(success_data), 200
    except NotFoundError as e:
        print(f"[DELETE /{word_id}] User {g.user_id} - Word not found: {str(e)}")
        return jsonify({"error": str(e)}), e.status_code  # 404
    except WordServiceError as e:
        print(
            f"[DELETE /{word_id}] User {g.user_id} - Service error: {e.message} | Context: {e.context}"
        )
        return jsonify({"error": e.message, "context": e.context}), e.status_code  # 500
    except Exception as e:
        print(f"[DELETE /{word_id}] User {g.user_id} - Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected server error occurred."}), 500


@words_bp.route("/<word_id>/star", methods=["POST"])
def star_word(word_id):
    try:
        success_data = ws.star_word_for_user(g.db, g.user_id, word_id)
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


@words_bp.route("/<word_id>/descriptions", methods=["POST"])
def add_description_to_word(word_id: str):
    try:
        request_data = request.get_json()
        description_text = request_data.get("description")
        if not description_text or not description_text.strip():
            return jsonify(
                {"error": "Missing or empty 'description' field in JSON body"}
            ), 400
        description_text = description_text.strip()
        success_data = ws.add_description_for_user(
            g.db, g.user_id, word_id, description_text
        )
        return jsonify(success_data), 200
    except NotFoundError as e:
        print(f"ROUTE: Word not found - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code  # 404
    except ForbiddenError as e:
        print(f"ROUTE: Forbidden to add a description to word - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code  # 403
    except WordServiceError as e:
        print(f"ROUTE: WordServiceError - {str(e)}")
        return jsonify({"error": e.message, "context": e.context}), e.status_code  # 500
    except Exception as e:
        print(
            f"ROUTE: Unexpected error in add_description_for_user for word_id {word_id}: {str(e)}"
        )
        return jsonify({"error": "An unexpected server error occurred."}), 500


@words_bp.route("/<word_id>/examples", methods=["POST"])
def add_example_to_word(word_id: str):
    try:
        request_data = request.get_json()
        example_text = request_data.get("example")
        if not example_text or not example_text.strip():
            return jsonify(
                {"error": "Missing or empty 'example' field in JSON body"}
            ), 400
        example_text = example_text.strip()
        success_data = ws.add_example_for_user(g.db, g.user_id, word_id, example_text)
        return jsonify(success_data), 200
    except NotFoundError as e:
        print(f"ROUTE: Word not found - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code  # 404
    except ForbiddenError as e:
        print(f"ROUTE: Forbidden to add a example to word - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code  # 403
    except WordServiceError as e:
        print(f"ROUTE: WordServiceError - {str(e)}")
        return jsonify({"error": e.message, "context": e.context}), e.status_code  # 500
    except Exception as e:
        print(
            f"ROUTE: Unexpected error in add_example_for_user for word_id {word_id}: {str(e)}"
        )
        return jsonify({"error": "An unexpected server error occurred."}), 500
