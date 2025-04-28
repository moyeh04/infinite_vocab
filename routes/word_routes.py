from firebase_admin import auth
from flask import Blueprint, jsonify, request

words_bp = Blueprint("words_api", __name__)


@words_bp.route("/", methods=["GET"])
def list_words():
    return jsonify({"message": "Word routes /all GET endpoint reached"})


@words_bp.route("/", methods=["POST"])
def create_word():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Authorization header missing or invalid format"}), 401

    try:
        id_token = auth_header[7:]
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token["uid"]
        print(f"Successfully verfied token for UID: {uid}")

    except Exception as e:
        print(f"Error verifying Firebase ID token: {e}")

        return jsonify({"error": "Invalid or expired authentication token"}), 401

    request_data = request.get_json()
    if not request_data:
        return jsonify({"error": "Missing or invalid JSON request body"}), 400

    word = request_data.get("word")

    if not word or not word.strip():
        return jsonify(
            {"error": "Missing or empty 'word_text' field in JSON body"}
        ), 400

    print(f"Input validation passed. Word to add: {word}")

    return jsonify({"message": "Word routes /add POST endpoint reached"})
