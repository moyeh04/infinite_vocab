"""Admin routes - Endpoints for administrative tasks."""

from flask import Blueprint, g, jsonify, request

from middleware import admin_required, firebase_token_required
from schemas import RoleUpdateSchema
from services import admin_service
from utils import AdminServiceError, DuplicateEntryError, NotFoundError, ValidationError

admin_bp = Blueprint("admin_api", __name__, url_prefix="/api/v1/admin")


@admin_bp.before_request
def apply_admin_auth():
    """Apply both authentication and admin authorization to all routes."""
    # First, ensure the user is authenticated with a valid token.
    auth_error = firebase_token_required()
    if auth_error:
        return auth_error

    # THEN, ensure the authenticated user is an admin.
    admin_error = admin_required()
    if admin_error:
        return admin_error


@admin_bp.route("/users", methods=["GET"])
def list_all_users_route():
    """Endpoint for an admin to get a list of all users."""
    try:
        all_users = admin_service.get_all_users(g.db)
        # Convert the list of Pydantic models to a list of dicts for JSON response
        return jsonify([user.model_dump(by_alias=True) for user in all_users]), 200
    except AdminServiceError as e:
        return jsonify({"error": str(e)}), 500


# NOTE on First Admin: The very first admin must be created manually in the Firestore
# 'admins' collection by a developer. This endpoint allows that first admin
# (and any subsequent admins) to promote other users through the API.
@admin_bp.route("/users/<user_id_to_promote>/promote", methods=["POST"])
def promote_user_route(user_id_to_promote: str):
    """Promotes a specified user to an admin role."""
    try:
        current_admin_id = g.user_id
        result = admin_service.add_admin_privileges(
            g.db, user_id_to_promote, current_admin_id
        )
        return jsonify(result), 200
    except NotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except DuplicateEntryError as e:
        return jsonify({"error": str(e)}), 409
    except AdminServiceError as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/users/<user_id>/role", methods=["PATCH"])
def update_role_route(user_id: str):
    """Updates the role of an existing admin."""
    try:
        schema = RoleUpdateSchema(**request.get_json())
        result = admin_service.update_admin_role(g.db, user_id, schema)
        return jsonify(result), 200
    except (ValidationError, ValueError) as e:
        return jsonify({"error": f"Invalid input: {e}"}), 400
    except NotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except AdminServiceError as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/users/<user_id_to_demote>/demote", methods=["DELETE"])
def demote_user_route(user_id_to_demote: str):
    """Revokes a user's admin privileges."""
    try:
        result = admin_service.remove_admin_privileges(g.db, user_id_to_demote)
        return jsonify(result), 200
    except NotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except AdminServiceError as e:
        return jsonify({"error": str(e)}), 500
