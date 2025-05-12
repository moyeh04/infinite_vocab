from firebase_admin import auth, firestore
from flask import Blueprint, g, jsonify, request

words_bp = Blueprint("words_api", __name__)

@words_bp.before_request
def authenticate_before_request():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Authorization header missing or invalid format"}), 401

    try:
        id_token = auth_header[7:]  # Or split(' ')[1]
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token["uid"]
        g.user_id = uid
        print(f"Successfully verfied token for UID: {uid}")

    except Exception as e:
        print(f"Error verifying Firebase ID token: {e}")

        return jsonify({"error": "Invalid or expired authentication token"}), 401

@words_bp.route("/", methods=["GET"])
def list_words():
    return jsonify({"message": "Word routes /all GET endpoint reached"})


@words_bp.route("/", methods=["POST"])
def create_word():
    uid = g.user_id

    request_data = request.get_json()
    if not request_data:
        return jsonify({"error": "Missing or invalid JSON request body"}), 400

    word = request_data.get("word")

    if not word or not word.strip():
        return jsonify({"error": "Missing or empty 'word' field in JSON body"}), 400

    word = word.strip()
    print(f"Input validation passed. Word to add: {word}")

    db = firestore.client()

    existing_words_query = (
        db.collection("words")
        .where(filter=firestore.FieldFilter("user_uid", "==", uid))
        .where(filter=firestore.FieldFilter("word", "==", word))
        .limit(1)
    )
    existing_words = list(existing_words_query.stream())

    if existing_words:
        existing_doc_id = existing_words[0].id
        print("--------------------------------------------------")
        print(
            f"Duplicate found: Word '{word}' already exists for user '{uid}' (Existing Doc ID: {existing_doc_id})."
        )
        print("--------------------------------------------------")
        return jsonify(
            {
                "message": f"Word '{word}' already exists in your list. Try adding a star to the existing entry instead?",
                "existing_word_id": existing_doc_id,
            }
        ), 409

    data_to_save = {
        "word": word,
        "stars": 0,
        "user_uid": uid,
        "createdAt": firestore.SERVER_TIMESTAMP,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    }

    try:
        _, words_ref = db.collection("words").add(data_to_save)
        print(f"Word added to Firestore with ID: {words_ref.id}")
        response_data = data_to_save.copy()
        response_data["word_id"] = words_ref.id

        # Remove createdAt/updatedAt fields because they hold SERVER_TIMESTAMP
        # sentinels which cannot be directly converted to JSON by jsonify.
        del response_data["createdAt"]
        del response_data["updatedAt"]
        return jsonify(response_data), 201

    except Exception as e:
        print(f"Error saving word to Firestore: {e}")
        return jsonify({"error": "Error saving word to database"}), 500
