"""User routes - HTTP endpoints for user operations."""

import logging

from flask import Blueprint, g, jsonify, request

from middleware import firebase_token_required
from schemas import UserCreateSchema, UserUpdateSchema
from services import user_service
from utils import NotFoundError, UserServiceError, ValidationError

logger = logging.getLogger("infinite_vocab_app")
user_bp = Blueprint("user_api", __name__, url_prefix="/api/v1/users")


@user_bp.before_request
def authentication_before_request():
    """Apply Firebase token authentication to all routes in this blueprint."""
    # Log request BEFORE authentication
    logger.info(f"REQUEST: {request.method} {request.path}")
    return firebase_token_required()


@user_bp.route("/", methods=["POST"])
def get_or_create_user_route():
    """
    Handles initial user sign-in.
    Returns 201 if a new user is created, 200 if an existing user is retrieved.
    """
    logger.info(f"ROUTE: get_or_create_user_route invoked for user_id: {g.user_id}")
    try:
        schema = UserCreateSchema(**request.get_json())
        user, was_created = user_service.get_or_create_user(g.db, g.user_id, schema)
        status_code = 201 if was_created else 200
        logger.info(
            f"ROUTE: User processed for user_id: {g.user_id}. New user created: {was_created}."
        )
        return jsonify(user.model_dump(by_alias=True)), status_code
    except (ValidationError, ValueError) as e:
        logger.warning(
            f"ROUTE: Validation error for user_id {g.user_id} on user creation: {e}"
        )
        return jsonify({"error": f"Invalid input: {e}"}), 400
    except UserServiceError as e:
        logger.error(
            f"ROUTE: Service error for user_id {g.user_id} on user creation: {e}"
        )
        return jsonify({"error": str(e)}), 500


@user_bp.route("/me", methods=["GET"])
def get_my_profile_route():
    """Fetches the profile of the currently authenticated user."""
    logger.info(f"ROUTE: get_my_profile_route invoked for user_id: {g.user_id}")
    try:
        user = user_service.get_user_profile(g.db, g.user_id)
        return jsonify(user.model_dump(by_alias=True)), 200
    except NotFoundError as e:
        logger.warning(f"ROUTE: Profile not found for user_id {g.user_id}: {e}")
        return jsonify({"error": str(e)}), 404
    except UserServiceError as e:
        logger.error(
            f"ROUTE: Service error getting profile for user_id {g.user_id}: {e}"
        )
        return jsonify({"error": str(e)}), 500


@user_bp.route("/me", methods=["PATCH"])
def update_my_profile_route():
    """Updates the profile of the currently authenticated user."""
    logger.info(f"ROUTE: update_my_profile_route invoked for user_id: {g.user_id}")
    try:
        schema = UserUpdateSchema(**request.get_json())
        user = user_service.update_user_profile(g.db, g.user_id, schema)
        logger.info(f"ROUTE: Successfully updated profile for user_id: {g.user_id}")
        return jsonify(user.model_dump(by_alias=True)), 200
    except (ValidationError, ValueError) as e:
        logger.warning(
            f"ROUTE: Validation error updating profile for user_id {g.user_id}: {e}"
        )
        return jsonify({"error": f"Invalid input: {e}"}), 400
    except NotFoundError as e:
        logger.warning(
            f"ROUTE: Profile not found for update for user_id {g.user_id}: {e}"
        )
        return jsonify({"error": str(e)}), 404
    except UserServiceError as e:
        logger.error(
            f"ROUTE: Service error updating profile for user_id {g.user_id}: {e}"
        )
        return jsonify({"error": str(e)}), 500


@user_bp.route("/me/score-history", methods=["GET"])
def get_my_score_history_route():
    """Fetches the score history for the currently authenticated user."""
    logger.info(f"ROUTE: get_my_score_history_route invoked for user_id: {g.user_id}")
    try:
        history = user_service.get_score_history_for_user(g.db, g.user_id)
        return jsonify([entry.model_dump(by_alias=True) for entry in history]), 200
    except UserServiceError as e:
        logger.error(
            f"ROUTE: Service error getting score history for user {g.user_id}: {e}"
        )
        return jsonify({"error": str(e)}), 500


@user_bp.route("/leaderboard", methods=["GET"])
def get_leaderboard_route():
    """Fetches the top users by score for the leaderboard."""
    logger.info("ROUTE: get_leaderboard_route invoked.")

    try:
        # We can add a query param to control the limit in the future if needed

        limit = request.args.get("limit", default=20, type=int)
        leaderboard = user_service.get_leaderboard(g.db, limit)

        # We only want to return specific fields for the leaderboard

        leaderboard_data = [
            {
                "userName": user.user_name,
                "userCode": user.user_code,
                "totalScore": user.total_score,
            }
            for user in leaderboard
        ]
        return jsonify(leaderboard_data), 200
    except UserServiceError as e:
        logger.error(f"ROUTE: Service error getting leaderboard: {e}")
        return jsonify({"error": str(e)}), 500
