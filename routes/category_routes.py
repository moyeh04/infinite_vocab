"""Category routes - HTTP endpoints for category CRUD operations"""

import logging

from flask import Blueprint, g, jsonify, request

from middleware import firebase_token_required
from schemas import CategoryCreateSchema, CategoryUpdateSchema
from services import category_service as cs
from utils import CategoryServiceError, NotFoundError, ValidationError

logger = logging.getLogger("infinite_vocab_app")
category_bp = Blueprint("category", __name__, url_prefix="/api/v1/categories")


@category_bp.before_request
def authenticate_before_request():
    # Log request BEFORE authentication
    logger.info(f"REQUEST: {request.method} {request.path}")
    return firebase_token_required()


@category_bp.route("/", methods=["POST"])
def create_category_route():
    """Create a new category for a user"""
    logger.info(f"ROUTE: create_category_route invoked for user_id: {g.user_id}")
    try:
        data = request.get_json()
        schema = CategoryCreateSchema(**data)
        category = cs.create_category(db=g.db, user_id=g.user_id, schema=schema)
        logger.info(
            f"ROUTE: Successfully created category '{category.category_id}' for user_id: {g.user_id}"
        )

        response = jsonify(category.model_dump(by_alias=True)), 201
        logger.info(f"RESPONSE: {request.path} - Status: 201")
        return response
    except CategoryServiceError as e:
        logger.warning(
            f"ROUTE: Business rule violation for user {g.user_id} creating category: {e}"
        )
        return jsonify({"error": str(e)}), 400

    except (ValidationError, ValueError) as e:
        logger.warning(
            f"ROUTE: Validation error for user {g.user_id} creating category: {e}"
        )
        return jsonify({"error": f"Invalid input: {e}"}), 400
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error creating category for user {g.user_id}: {e}"
        )
        return jsonify({"error": "Internal server error"}), 500


@category_bp.route("/", methods=["GET"])
def get_categories_route():
    """Get all categories for authenticated user"""
    logger.info(f"ROUTE: get_categories_route invoked for user_id: {g.user_id}")
    try:
        categories = cs.get_categories_by_user(g.db, g.user_id)
        return jsonify([c.model_dump(by_alias=True) for c in categories]), 200
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error getting categories for user {g.user_id}: {e}"
        )
        return jsonify({"error": "Internal server error"}), 500


@category_bp.route("/<category_id>", methods=["GET"])
def get_category_route(category_id):
    """Get a specific category by ID for authenticated user"""
    logger.info(
        f"ROUTE: get_category_route invoked for user {g.user_id} and category {category_id}"
    )
    try:
        category = cs.get_category_by_id(g.db, category_id, g.user_id)
        return jsonify(category.model_dump(by_alias=True)), 200
    except NotFoundError as e:
        logger.warning(
            f"ROUTE: Not found error for user {g.user_id} getting category {category_id}: {e}"
        )
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error getting category {category_id} for user {g.user_id}: {e}"
        )
        return jsonify({"error": "Internal server error"}), 500


@category_bp.route("/<category_id>", methods=["PUT"])
def update_category_route(category_id):
    """Update a category for authenticated user"""
    logger.info(
        f"ROUTE: update_category_route invoked for user {g.user_id} and category {category_id}"
    )
    try:
        data = request.get_json()
        schema = CategoryUpdateSchema(**data)
        category = cs.update_category(g.db, category_id, g.user_id, schema)
        logger.info(
            f"ROUTE: Successfully updated category {category_id} for user {g.user_id}"
        )
        return jsonify(category.model_dump(by_alias=True)), 200
    except CategoryServiceError as e:
        logger.warning(
            f"ROUTE: Business rule violation for user {g.user_id} updating category {category_id}: {e}"
        )
        return jsonify({"error": str(e)}), 400
    except NotFoundError as e:
        logger.warning(
            f"ROUTE: Not found error for user {g.user_id} updating category {category_id}: {e}"
        )
        return jsonify({"error": str(e)}), 404
    except (ValidationError, ValueError) as e:
        logger.warning(
            f"ROUTE: Validation error for user {g.user_id} updating category {category_id}: {e}"
        )
        return jsonify({"error": f"Invalid input: {str(e)}"}), 400
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error updating category {category_id} for user {g.user_id}: {e}"
        )
        return jsonify({"error": "Internal server error"}), 500


@category_bp.route("/<category_id>", methods=["DELETE"])
def delete_category_route(category_id):
    """Delete a category for authenticated user"""
    logger.info(
        f"ROUTE: delete_category_route invoked for user {g.user_id} and category {category_id}"
    )
    try:
        cs.delete_category(g.db, category_id, g.user_id)
        logger.info(
            f"ROUTE: Successfully deleted category {category_id} for user {g.user_id}"
        )
        return jsonify({"message": "Category deleted successfully"}), 200
    except NotFoundError as e:
        logger.warning(
            f"ROUTE: Not found error for user {g.user_id} deleting category {category_id}: {e}"
        )

        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error deleting category {category_id} for user {g.user_id}: {e}"
        )
        return jsonify({"error": "Internal server error"}), 500
