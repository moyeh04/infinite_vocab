"""Middleware for handling Firebase JWT authentication and role-based access control."""

import logging
from functools import wraps

from firebase_admin import auth, firestore
from flask import g, jsonify, request

logger = logging.getLogger("infinite_vocab_app")


def firebase_token_required():
    """A standard function to be used in `before_request` hooks."""
    if request.method == "OPTIONS":
        return None  # CORS handles this, no need for 200 code response
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning("AUTH: Authorization header missing or invalid.")

        return jsonify({"error": "Authorization header missing or invalid format"}), 401
    try:
        id_token = auth_header.split("Bearer ")[1]
        decoded_token = auth.verify_id_token(id_token)
        g.user_id = decoded_token["uid"]
        g.db = firestore.client()
        logger.info(f"AUTH: Token verified for user_id: {g.user_id}")

    except Exception as e:
        logger.error(f"AUTH: Error verifying Firebase ID token: {e}", exc_info=True)
        return jsonify({"error": "Invalid or expired authentication token"}), 401


def admin_required(f):
    """A decorator to protect routes that require admin privileges."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # This check assumes firebase_token_required has already run and set g.user_id
        if not hasattr(g, "user_id"):
            logger.error(
                "AUTH: Admin check failed - admin_required used without a user token.",
                exc_info=True,
            )
            return jsonify({"error": "Authentication token is required."}), 401

        try:
            admin_doc = g.db.collection("admins").document(g.user_id).get()
            if not admin_doc.exists:
                logger.warning(
                    f"AUTH: Admin check failed - User {g.user_id} is not an admin."
                )
                return jsonify(
                    {"error": "Forbidden: Admin privileges are required."}
                ), 403

            g.admin_role = admin_doc.to_dict().get("role", "admin")
            logger.info(f"AUTH: User {g.user_id} is an admin with role: {g.admin_role}")
        except Exception as e:
            logger.error(
                f"AUTH: DB error checking admin status for user {g.user_id}: {e}",
                exc_info=True,
            )
            return jsonify(
                {"error": "An internal error occurred while verifying permissions."}
            ), 500

        return f(*args, **kwargs)

    return decorated_function


def super_admin_required(f):
    """A decorator to protect routes that require super-admin privileges."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # This decorator should be stacked on top of @admin_required, so g.admin_role will exist.
        if not hasattr(g, "admin_role"):
            logger.error(
                "AUTH: Super admin check failed - super_admin_required called out of order.",
                exc_info=True,
            )
            # This is a fallback, but the main check in admin_required should have caught it.
            return jsonify({"error": "Forbidden: Admin privileges are required."}), 403

        if g.admin_role != "super-admin":
            logger.warning(
                f"AUTH: Super admin check failed - User {g.user_id} has role '{g.admin_role}', but 'super-admin' is required."
            )
            return jsonify(
                {
                    "error": "Forbidden: Super-admin privileges are required for this action."
                }
            ), 403

        logger.info(f"AUTH: User {g.user_id} verified as super-admin.")
        return f(*args, **kwargs)

    return decorated_function


def resolve_user_by_code(param_name: str):
    """
    Decorator that finds a user by a `user_code` from the URL.

    This performs a direct database lookup for the user, handles the not
    found case, and attaches the resolved `target_user_id` to the Flask `g`
    object for use within the decorated route. It is self-contained and
    does not call the service layer.

    Args:
        param_name: The name of the URL keyword argument holding the user_code.
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_code = kwargs.get(param_name)
            if not user_code:
                # This is a developer configuration error.
                logger.error(
                    f"DEV_ERROR: `resolve_user_by_code` decorator used with invalid param_name '{param_name}'.",
                    exc_info=True,
                )
                return jsonify({"error": "Server configuration error."}), 500

            try:
                users_ref = g.db.collection("users")
                query = users_ref.where("user_code", "==", user_code).limit(1)
                docs = list(query.stream())

                if not docs:
                    logger.warning(
                        f"AUTH: User with code '{user_code}' not found by admin {g.user_id}."
                    )
                    return jsonify(
                        {"error": f"User with code '{user_code}' not found."}
                    ), 404

                target_user_doc = docs[0]
                g.target_user_id = target_user_doc.id
                # Store the code on `g` as well, for consistent logging in the route.
                g.target_user_code = user_code

            except Exception as e:
                logger.error(
                    f"DB_ERROR: Failed lookup for user_code '{user_code}' by admin {g.user_id}: {e}",
                    exc_info=True,
                )
                return jsonify(
                    {"error": "A database error occurred while finding the user."}
                ), 500

            return f(*args, **kwargs)

        return decorated_function

    return decorator
