from firebase_admin import firestore
from flask import Blueprint, g, jsonify, request

from middleware.firebase_auth_check import firebase_token_required
from services.word_service import create_word_for_user
from utils.exceptions import (
    DatabaseError,
    DuplicateEntryError,
    WordServiceError,
)

words_bp = Blueprint("words_api", __name__, url_prefix="/api/v1/words")


@words_bp.before_request
def authenticate_before_request():
    return firebase_token_required()


@firestore.transactional
def _atomic_update(transaction, doc_ref_to_update, current_user_uid):
    # Read
    snapshot = doc_ref_to_update.get(transaction=transaction)

    if not snapshot.exists:
        return "NOT_FOUND"

    word_data = snapshot.to_dict()

    if word_data.get("user_uid") != current_user_uid:
        return "FORBIDDEN"

    word_text = word_data.get("word")

    # Modify
    current_stars = word_data.get("stars", 0)
    new_star_count = current_stars + 1

    # Write
    transaction.update(
        doc_ref_to_update,
        {"stars": new_star_count, "updatedAt": firestore.SERVER_TIMESTAMP},
    )
    return (new_star_count, word_text)


@words_bp.route("/<word_id>/star", methods=["POST"])
def star_word(word_id):
    uid = g.user_id
    db = firestore.client()
    transaction = db.transaction()

    try:
        word_doc_ref = db.collection("words").document(word_id)

        result, word_text = _atomic_update(transaction, word_doc_ref, uid)

        if result == "NOT_FOUND":
            return jsonify({"error": f"Word with ID '{word_id}'"}), 404
        if result == "FORBIDDEN":
            return jsonify(
                {"error": "You are not authorized to star this word"}
            ), 403

        print(
            f"STAR_WORD: Star updated for word ID '{word_id}' (text: '{word_text}') for UID: {uid}. New stars: {result}"
        )

        return jsonify(
            {
                "message": f"Successfully starred word '{word_text}'.",
                "word_id": word_id,
                "new_star_count": result,
            }
        ), 200

    except Exception as e:
        print(
            f"STAR_WORD: Error starring word ID '{word_id}' for UID {uid}: {str(e)}"
        )
        return jsonify(
            {"error": "An error occurred while starring the word"}
        ), 500


@words_bp.route("/", methods=["GET"])
def list_words():
    uid = g.user_id
    print(f"LIST_WORDS: Attempting to fetch words for UID: {uid}")

    try:
        db = firestore.client()
        print("LIST_WORDS: Firestore client obtained.")

        words_query = (
            db.collection("words")
            .where(filter=firestore.FieldFilter("user_uid", "==", uid))
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
        print(f"LIST_WORDS: Error fetching words for user {uid}: {str(e)}")
        return jsonify(
            {"error": "An error occurred while fetching words."}
        ), 500


@words_bp.route("/", methods=["POST"])
def create_word():
    uid = g.user_id

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

    db = firestore.client()
    try:
        new_word_details = create_word_for_user(db, uid, word)

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
