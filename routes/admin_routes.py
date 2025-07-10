"""Admin routes - Endpoints for administrative tasks."""

from flask import Blueprint, g, jsonify, request

from middleware import admin_required, firebase_token_required, super_admin_required
from schemas import RoleUpdateSchema
from services import admin_service
from utils import AdminServiceError, DuplicateEntryError, NotFoundError, ValidationError

admin_bp = Blueprint("admin_api", __name__, url_prefix="/api/v1/admin")


@admin_bp.before_request
def admin_before_request():
    """Ensure all admin routes require authentication and admin privileges."""
    # Check authentication first
    auth_result = firebase_token_required()
    if auth_result:
        return auth_result

    # Check admin status
    admin_result = admin_required()
    if admin_result:
        return admin_result


@admin_bp.route("/users", methods=["GET"])
def list_all_users_route():
    """Endpoint for an admin to get a list of all users. Accessible by: admin, super-admin"""
    try:
        all_users = admin_service.get_all_users(g.db)
        return jsonify([user.model_dump(by_alias=True) for user in all_users]), 200
    except AdminServiceError as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/users/<user_id_to_promote>/promote", methods=["POST"])
def promote_user_route(user_id_to_promote: str):
    """Promotes a specified user to an admin role. Accessible by: super-admin ONLY"""
    # Check super-admin for this specific route
    super_admin_result = super_admin_required()
    if super_admin_result:
        return super_admin_result

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
    """Updates the role of an existing admin. Accessible by: super-admin ONLY"""
    # Check super-admin for this specific route
    super_admin_result = super_admin_required()
    if super_admin_result:
        return super_admin_result

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
    """Revokes a user's admin privileges. Accessible by: super-admin ONLY"""
    # Check super-admin for this specific route
    super_admin_result = super_admin_required()
    if super_admin_result:
        return super_admin_result

    try:
        result = admin_service.remove_admin_privileges(g.db, user_id_to_demote)
        return jsonify(result), 200
    except NotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except AdminServiceError as e:
        return jsonify({"error": str(e)}), 500
