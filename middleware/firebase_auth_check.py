from firebase_admin import auth, firestore
from flask import g, jsonify, request


def firebase_token_required():
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
        print(f"AUTH_MIDDLEWARE: Token verified for UID: {uid}")

    except Exception as e:
        print(f"Error verifying Firebase ID token: {e}")

        return jsonify(
            {"error": "Invalid or expired authentication token"}
        ), 401
