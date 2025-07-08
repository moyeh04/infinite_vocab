from firebase_admin import auth, firestore
from flask import g, request

from utils.response_helpers import error_response


def firebase_token_required():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return error_response("Authorization header missing or invalid format", 401)

    try:
        id_token = auth_header[7:]  # Or split(' ')[1]
        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token["uid"]
        g.user_id = user_id
        g.db = firestore.client()
        print(f"AUTH_MIDDLEWARE: Token verified for user_id: {user_id}")

    except Exception as e:
        print(f"Error verifying Firebase ID token: {e}")

        return error_response("Invalid or expired authentication token", 401)
