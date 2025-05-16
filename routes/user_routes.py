from flask import Blueprint, g, jsonify, request

from middleware.firebase_auth_check import firebase_token_required
from services.user_service import get_or_create_user_code as usr_code

user_bp = Blueprint("user_api", __name__, url_prefix="/api/v1/users")


@user_bp.before_request
def authentication_before_request():
    return firebase_token_required()


@user_bp.route("/", methods=["POST"])
def generate_user():
    uid = g.user_id
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify(
                {"error": "Missing or invalid JSON request body"}
            ), 400

        user_name = request.json.get("name")
        if not user_name or not user_name.strip():
            return jsonify({"error": "Missing or empty 'name' field"}), 400

        user_name = user_name.strip()

        # --- Call the user service to get or create the user's application code ---
        user_code = usr_code(uid, user_name)

        # --- Check if the user service returned a valid code ---
        if user_code is None:
            # If the service function returned None, it means there was an error getting/creating the code
            print(f"Error: Failed to get or create user code for UID {uid}.")
            # Return a 500 Internal Server Error to indicate a server-side problem
            return jsonify(
                {"error": "Failed to retrieve or create user data"}
            ), 500

        return jsonify(
            {
                "message": "User authenticated successfully",
                "uid": uid,
                "name": user_name,
                "userCode": user_code,
            }
        ), 201
    except Exception as e:
        print(
            f"Unexpected error in generate_user for UID {uid if 'uid' in locals() else 'unknown'}: {str(e)}"
        )
        return jsonify({"error": "An unexpected server error occurred"}), 500
