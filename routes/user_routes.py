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
