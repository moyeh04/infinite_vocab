from firebase_admin import auth, firestore
from flask import Blueprint, g, jsonify, request

words_bp = Blueprint("words_api", __name__)


@words_bp.before_request
def authenticate_before_request():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify(
            {"error": "Authorization header missing or invalid format"}
        ), 401

    try:
        id_token = auth_header[7:]  # Or split(' ')[1]
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token["uid"]
        g.user_id = uid
        g.db = firestore.client()
        print(f"Successfully verfied token for UID: {uid}")

    except Exception as e:
        print(f"Error verifying Firebase ID token: {e}")

        return jsonify(
            {"error": "Invalid or expired authentication token"}
        ), 401


@words_bp.route("/", methods=["PUT"])
def star_word():
    uid = g.user_id
    db = firestore.client()
    request_data = request.get_json()
    if not request_data:
        return jsonify({"error": "Missing or invalid JSON request body"}), 400

    try:
        word = request_data.get("word")
        word_query = (
            db.collection("words")
            .where(filter=firestore.FieldFilter("user_uid", "==", uid))
            .where(filter=firestore.FieldFilter("word", "==", word))
            .limit(1)
        )
        print(word_query)
        updatequery = list(word_query.stream())
        print(updatequery)
        if not updatequery:
            return jsonify({"error": "No word foudn"}), 200
        nouble_of_stars = updatequery[0].to_dict()["stars"]
        print(nouble_of_stars)
        nouble_of_stars += 1
        data_to_update = {"stars": nouble_of_stars}
        print(nouble_of_stars)
        _ = (
            db.collection("words")
            .document(updatequery[0].id)
            .update(data_to_update)
        )
        print(f"STAR_WORD: Attempting to star word {db} for UID: {uid}")
        return jsonify({"good": "good"})
    except Exception as e:
        return jsonify({"error": f"error {e}"})


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
            word_data["id"] = document_snapshot.id
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
