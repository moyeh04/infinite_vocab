from firebase_admin import firestore
from flask import Blueprint, g, jsonify, request

from middleware.firebase_auth_check import firebase_token_required
from services.word_service import create_word_for_user, star_word_for_user
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
        return jsonify(
            {"error": e.message, "context": e.context}
        ), e.status_code  # 500
    except Exception as e:
        print(
            f"ROUTE: Unexpected error in star_word for word_id {word_id}: {str(e)}"
        )
        return jsonify({"error": "An unexpected server error occurred."}), 500


@words_bp.route("/", methods=["GET"])
def list_words():
    print(f"LIST_WORDS: Attempting to fetch words for UID: {g.user_id}")

    try:
        print("LIST_WORDS: Firestore client obtained.")

        words_query = (
            g.db.collection("words")
            .where(filter=firestore.FieldFilter("user_uid", "==", g.user_id))
            .order_by(field_path="stars", direction="DESCENDING")
        )
        print("LIST_WORDS: Query built.")

        word_snapshots = list(words_query.stream())
        print(f"LIST_WORDS: Found {len(word_snapshots)} word snapshot(s).")

        results_list = []
        for document_snapshot in word_snapshots:
            word_data = document_snapshot.to_dict()
            if word_data is None:
                print(
                    f"LIST_WORDS: Warning - Document {document_snapshot.id} has no data (to_dict() returned None). Skipping."
                )
                continue
            word_data["word_id"] = document_snapshot.id
            results_list.append(word_data)

        print(
            f"LIST_WORDS: Prepared results_list with {len(results_list)} items."
        )
        # print(f"LIST_WORDS: Full results_list: {results_list}") # Optional: very verbose for many words
        return jsonify(results_list), 200

    except Exception as e:
        print(
            f"LIST_WORDS: Error fetching words for user {g.user_id}: {str(e)}"
        )
        return jsonify(
            {"error": "An error occurred while fetching words."}
        ), 500


@words_bp.route("/", methods=["POST"])
def create_word():
    request_data = request.get_json()
    if not request_data:
        return jsonify({"error": "Missing or invalid JSON request body"}), 400

    word = request_data.get("word")

    if not word or not word.strip():
        return jsonify(
            {"error": "Missing or empty 'word' field in JSON body"}
        ), 400

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
        return jsonify(
            {"error": e.message, "context": e.context}
        ), e.status_code

    except Exception as e:
        # This 'uid' might not be available if the error happened before it was set in this scope.
        # The one in g.user_id should be from the before_request hook.
        print(
            f"ROUTE: Unexpected error in create_word for UID {g.user_id if hasattr(g, 'user_id') else 'unknown'}: {str(e)}"
        )
        return jsonify({"error": "An unexpected server error occurred."}), 500
