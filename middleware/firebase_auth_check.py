"""Middleware for handling Firebase JWT authentication and role-based access control."""

import logging
from functools import wraps

from firebase_admin import auth, firestore
from flask import g, request

from utils import error_response

logger = logging.getLogger("infinite_vocab_app")


def firebase_token_required():
    """A standard function to be used in `before_request` hooks."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning("AUTH: Authorization header missing or invalid.")

        return error_response("Authorization header missing or invalid format", 401)
    try:
        id_token = auth_header.split("Bearer ")[1]
        decoded_token = auth.verify_id_token(id_token)
        g.user_id = decoded_token["uid"]
        g.db = firestore.client()
        logger.info(f"AUTH: Token verified for user_id: {g.user_id}")

    except Exception as e:
        logger.error(f"AUTH: Error verifying Firebase ID token: {e}", exc_info=True)
        return error_response("Invalid or expired authentication token", 401)


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
            return error_response("Authentication token is required.", 401)

        try:
            admin_doc = g.db.collection("admins").document(g.user_id).get()
            if not admin_doc.exists:
                logger.warning(
                    f"AUTH: Admin check failed - User {g.user_id} is not an admin."
                )
                return error_response("Forbidden: Admin privileges are required.", 403)

            g.admin_role = admin_doc.to_dict().get("role", "admin")
            logger.info(f"AUTH: User {g.user_id} is an admin with role: {g.admin_role}")
        except Exception as e:
            logger.error(
                f"AUTH: DB error checking admin status for user {g.user_id}: {e}",
                exc_info=True,
            )
            return error_response(
                "An internal error occurred while verifying permissions.", 500
            )

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
            return error_response("Forbidden: Admin privileges are required.", 403)

        if g.admin_role != "super-admin":
            logger.warning(
                f"AUTH: Super admin check failed - User {g.user_id} has role '{g.admin_role}', but 'super-admin' is required."
            )
            return error_response(
                "Forbidden: Super-admin privileges are required for this action.", 403
            )

        logger.info(f"AUTH: User {g.user_id} verified as super-admin.")
        return f(*args, **kwargs)

    return decorated_function
