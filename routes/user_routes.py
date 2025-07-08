from flask import Blueprint, g, request

from middleware.firebase_auth_check import firebase_token_required
from services.user_service import get_or_create_user_code as get_user_code
from utils.response_helpers import (
    camelized_response,
    decamelized_request,
    error_response,
)

user_bp = Blueprint("user_api", __name__, url_prefix="/api/v1/users")


@user_bp.before_request
def authentication_before_request():
    return firebase_token_required()


@user_bp.route("/", methods=["POST"])
def generate_user():
    user_id = g.user_id
    try:
        request_data = request.get_json()
        if not request_data:
            return error_response("Missing or invalid JSON request body", 400)

        # Convert camelCase from frontend to snake_case for Python
        request_data = decamelized_request(request_data)

        user_name = request_data.get("user_name")
        if not user_name or not user_name.strip():
            return error_response("Missing or empty 'userName' field", 400)

        user_name = user_name.strip()

        # --- Call the user service to get or create the user's application code ---
        user_code = get_user_code(user_id, user_name)

        # --- Check if the user service returned a valid code ---
        if user_code is None:
            # If the service function returned None, it means there was an error getting/creating the code
            print(f"Error: Failed to get or create user code for user_id {user_id}.")
            # Return a 500 Internal Server Error to indicate a server-side problem
            return error_response("Failed to retrieve or create user data", 500)

        return camelized_response(
            {
                "message": "User authenticated successfully",
                "user_id": user_id,
                "user_name": user_name,
                "user_code": user_code,
            },
            201,
        )
    except Exception as e:
        print(
            f"Unexpected error in generate_user for user_id {user_id if 'user_id' in locals() else 'unknown'}: {str(e)}"
        )
        return error_response("An unexpected server error occurred", 500)
