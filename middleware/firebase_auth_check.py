"""Middleware for handling Firebase JWT authentication and role-based access control."""

from firebase_admin import auth, firestore
from flask import g, request

from utils import error_response


def firebase_token_required():
    """Function for before_request hooks - returns error response or None on success"""
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


def admin_required():
    """
    Checks if the authenticated user has admin privileges.
    This must be called AFTER firebase_token_required.
    Returns error response or None on success - stores admin role in g.admin_role
    """
    # This check is a safeguard in case the middleware is called out of order.
    if not hasattr(g, "user_id"):
        return error_response("Authentication token is required.", 401)
    try:
        admin_doc = g.db.collection("admins").document(g.user_id).get()
        if not admin_doc.exists:
            return error_response("Forbidden: Admin privileges are required.", 403)
        # Store role for next decorator - could be "admin" or "super-admin"
        g.admin_role = admin_doc.to_dict().get("role", "admin")
        print(
            f"ADMIN_MIDDLEWARE: Admin verified for user_id: {g.user_id}, role: {g.admin_role}"
        )
    except Exception as e:
        print(f"MIDDLEWARE: Error checking admin status for user {g.user_id}: {e}")
        return error_response(
            "An internal error occurred while verifying permissions.", 500
        )


def super_admin_required():
    """
    Checks if the authenticated admin has 'super-admin' privileges.
    This must be called AFTER admin_required.
    Returns error response or None on success - assumes g.admin_role is already set
    """
    if not hasattr(g, "admin_role") or g.admin_role != "super-admin":
        return error_response(
            "Forbidden: Super-admin privileges are required for this action.", 403
        )
    print(f"SUPER_ADMIN_MIDDLEWARE: Super-admin verified for user_id: {g.user_id}")
