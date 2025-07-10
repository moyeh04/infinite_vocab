"""Admin routes - Endpoints for administrative tasks."""

import logging

from flask import Blueprint, g, jsonify, request

from middleware import admin_required, firebase_token_required, super_admin_required
from schemas import RoleUpdateSchema, ScoreUpdateSchema
from services import admin_service
from utils import AdminServiceError, DuplicateEntryError, NotFoundError, ValidationError

logger = logging.getLogger("infinite_vocab_app")
admin_bp = Blueprint("admin_api", __name__, url_prefix="/api/v1/admin")


@admin_bp.before_request
def authentication_before_request():
    """This hook now only ensures a user is authenticated for all admin routes."""
    return firebase_token_required()


@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_all_users_route():
    """Endpoint for an admin to get a list of all users. Accessible by: admin, super-admin"""
    logger.info(f"ROUTE: Admin {g.user_id} requesting to list all users.")
    try:
        all_users = admin_service.get_all_users(g.db)
        logger.info(
            f"ROUTE: Successfully retrieved {len(all_users)} users for admin {g.user_id}."
        )
        return jsonify([user.model_dump(by_alias=True) for user in all_users]), 200

    except AdminServiceError as e:
        logger.error(f"ROUTE: Service error for admin {g.user_id} listing users: {e}")
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/users/<user_id_to_promote>/promote", methods=["POST"])
@admin_required
@super_admin_required
def promote_user_route(user_id_to_promote: str):
    """Promotes a specified user to an admin role. Accessible by: super-admin ONLY"""
    logger.info(
        f"ROUTE: Super-admin {g.user_id} attempting to promote user {user_id_to_promote}."
    )
    try:
        current_admin_id = g.user_id
        result = admin_service.add_admin_privileges(
            g.db, user_id_to_promote, current_admin_id
        )
        logger.info(
            f"ROUTE: Super-admin {g.user_id} successfully promoted user {user_id_to_promote}."
        )
        return jsonify(result), 200
    except NotFoundError as e:
        logger.warning(
            f"ROUTE: Super-admin {g.user_id} failed to promote non-existent user {user_id_to_promote}: {e}"
        )
        return jsonify({"error": str(e)}), 404
    except DuplicateEntryError as e:
        logger.warning(
            f"ROUTE: Super-admin {g.user_id} failed to promote user {user_id_to_promote} (already an admin): {e}"
        )
        return jsonify({"error": str(e)}), 409
    except AdminServiceError as e:
        logger.error(
            f"ROUTE: Service error while super-admin {g.user_id} promoting {user_id_to_promote}: {e}"
        )
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/users/<user_id>/role", methods=["PATCH"])
@admin_required
@super_admin_required
def update_role_route(user_id: str):
    """Updates the role of an existing admin. Accessible by: super-admin ONLY"""
    logger.info(
        f"ROUTE: Super-admin {g.user_id} attempting to update role for user {user_id}."
    )
    try:
        schema = RoleUpdateSchema(**request.get_json())
        result = admin_service.update_admin_role(g.db, user_id, schema)
        logger.info(
            f"ROUTE: Super-admin {g.user_id} successfully updated role for user {user_id}."
        )
        return jsonify(result), 200
    except (ValidationError, ValueError) as e:
        logger.warning(
            f"ROUTE: Super-admin {g.user_id} provided invalid data for role update on user {user_id}: {e}"
        )
        return jsonify({"error": f"Invalid input: {e}"}), 400
    except NotFoundError as e:
        logger.warning(
            f"ROUTE: Super-admin {g.user_id} failed to update role for non-existent admin {user_id}: {e}"
        )

        return jsonify({"error": str(e)}), 404
    except AdminServiceError as e:
        logger.error(
            f"ROUTE: Service error while super-admin {g.user_id} updating role for {user_id}: {e}"
        )
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/users/<user_id_to_demote>/demote", methods=["DELETE"])
@admin_required
@super_admin_required
def demote_user_route(user_id_to_demote: str):
    """Revokes a user's admin privileges. Accessible by: super-admin ONLY"""
    logger.info(
        f"ROUTE: Super-admin {g.user_id} attempting to demote user {user_id_to_demote}."
    )

    try:
        result = admin_service.remove_admin_privileges(g.db, user_id_to_demote)
        logger.info(
            f"ROUTE: Super-admin {g.user_id} successfully demoted user {user_id_to_demote}."
        )
        return jsonify(result), 200
    except NotFoundError as e:
        logger.warning(
            f"ROUTE: Super-admin {g.user_id} failed to demote non-existent admin {user_id_to_demote}: {e}"
        )
        return jsonify({"error": str(e)}), 404
    except AdminServiceError as e:
        logger.error(
            f"ROUTE: Service error while super-admin {g.user_id} demoting {user_id_to_demote}: {e}"
        )
        return jsonify({"error": str(e)}), 500


# Add these new routes to the end of routes/admin_routes.py


@admin_bp.route("/students", methods=["GET"])
@admin_required
def list_my_students_route():
    """Lists all students assigned to the authenticated admin."""
    logger.info(f"ROUTE: Admin {g.user_id} requesting their list of students.")
    try:
        students = admin_service.list_students_for_admin(g.db, g.user_id)
        return jsonify([user.model_dump(by_alias=True) for user in students]), 200
    except AdminServiceError as e:
        logger.error(
            f"ROUTE: Service error listing students for admin {g.user_id}: {e}"
        )
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/students/<student_id>", methods=["POST"])
@admin_required
def assign_student_route(student_id: str):
    """Assigns a student to the authenticated admin."""
    logger.info(f"ROUTE: Admin {g.user_id} attempting to assign student {student_id}.")
    try:
        result = admin_service.assign_student_to_admin(g.db, g.user_id, student_id)
        return jsonify(result), 200
    except (NotFoundError, DuplicateEntryError) as e:
        logger.warning(
            f"ROUTE: Client error for admin {g.user_id} assigning student {student_id}: {e}"
        )
        # 404 for student not found, 409 for student already taken
        status_code = 404 if isinstance(e, NotFoundError) else 409
        return jsonify({"error": str(e)}), status_code
    except AdminServiceError as e:
        logger.error(
            f"ROUTE: Service error for admin {g.user_id} assigning student {student_id}: {e}"
        )
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/students/<student_id>", methods=["DELETE"])
@admin_required
def remove_student_route(student_id: str):
    """Removes a student from the authenticated admin's management."""
    logger.info(f"ROUTE: Admin {g.user_id} attempting to remove student {student_id}.")
    try:
        result = admin_service.remove_student_from_admin(g.db, g.user_id, student_id)
        return jsonify(result), 200
    except NotFoundError as e:
        logger.warning(
            f"ROUTE: NotFound error for admin {g.user_id} removing student {student_id}: {e}"
        )
        return jsonify({"error": str(e)}), 404
    except AdminServiceError as e:
        logger.error(
            f"ROUTE: Service error for admin {g.user_id} removing student {student_id}: {e}"
        )
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/users/find", methods=["GET"])
@admin_required
def find_user_by_code_route():
    """Finds a user by their user_code."""
    user_code = request.args.get("code", "").strip()
    if not user_code:
        return jsonify({"error": "Query parameter 'code' is required."}), 400

    logger.info(f"ROUTE: Admin {g.user_id} is searching for user_code: {user_code}")
    try:
        user = admin_service.find_user_by_code(g.db, user_code)
        if not user:
            raise NotFoundError(f"User with code '{user_code}' not found.")
        return jsonify(user.model_dump(by_alias=True)), 200
    except NotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except AdminServiceError as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/students/<student_id>/score", methods=["POST"])
@admin_required
def add_score_route(student_id: str):
    """Adds an assessment score to a student managed by the admin."""
    logger.info(
        f"ROUTE: Admin {g.user_id} attempting to add score to student {student_id}."
    )
    try:
        schema = ScoreUpdateSchema(**request.get_json())
        result = admin_service.add_assessment_score(g.db, g.user_id, student_id, schema)
        return jsonify(result), 200
    except (ValidationError, ValueError) as e:
        return jsonify({"error": f"Invalid input: {e}"}), 400
    except NotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except AdminServiceError as e:
        return jsonify({"error": str(e)}), 500
