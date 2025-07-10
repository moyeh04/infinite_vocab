"""Category routes - HTTP endpoints for category CRUD operations"""

from flask import Blueprint, g, jsonify, request

from middleware import firebase_token_required
from schemas import CategoryCreateSchema, CategoryUpdateSchema
from services import category_service as cs
from utils import CategoryServiceError, NotFoundError

category_bp = Blueprint("category", __name__, url_prefix="/api/v1/categories")


@category_bp.before_request
def authenticate_before_request():
    return firebase_token_required()


@category_bp.route("/", methods=["POST"])
def create_category_route():
    """Create a new category for a user"""
    try:
        data = request.get_json()
        schema = CategoryCreateSchema(**data)
        category = cs.create_category(
            db=g.db,
            user_id=g.user_id,  # From authenticated token
            schema=schema,
        )
        return jsonify(category.model_dump(by_alias=True)), 201
    except CategoryServiceError as ce:
        return jsonify({"error": str(ce)}), 400
    except ValueError as ve:  # Pydantic validation errors
        return jsonify({"error": f"Invalid input: {str(ve)}"}), 400
    except Exception as e:
        print(f"CategoryRoutes: Unexpected error: {e}")

        return jsonify({"error": "Internal server error"}), 500


@category_bp.route("/", methods=["GET"])
def get_categories_route():
    """Get all categories for authenticated user"""
    try:
        categories = cs.get_categories_by_user(g.db, g.user_id)
        return jsonify([c.model_dump(by_alias=True) for c in categories]), 200
    except Exception as e:
        print(f"CategoryRoutes: Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@category_bp.route("/<category_id>", methods=["GET"])
def get_category_route(category_id):
    """Get a specific category by ID for authenticated user"""
    try:
        category = cs.get_category_by_id(g.db, category_id, g.user_id)
        return jsonify(category.model_dump(by_alias=True)), 200
    except NotFoundError as ne:
        return jsonify({"error": str(ne)}), 404
    except Exception as e:
        print(f"CategoryRoutes: Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@category_bp.route("/<category_id>", methods=["PUT"])
def update_category_route(category_id):
    """Update a category for authenticated user"""
    try:
        data = request.get_json()
        schema = CategoryUpdateSchema(**data)
        category = cs.update_category(g.db, category_id, g.user_id, schema)
        return jsonify(category.model_dump(by_alias=True)), 200
    except CategoryServiceError as ce:
        return jsonify({"error": str(ce)}), 400
    except NotFoundError as ne:
        return jsonify({"error": str(ne)}), 404
    except ValueError as ve:  # Pydantic validation errors
        return jsonify({"error": f"Invalid input: {str(ve)}"}), 400
    except Exception as e:
        print(f"CategoryRoutes: Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@category_bp.route("/<category_id>", methods=["DELETE"])
def delete_category_route(category_id):
    """Delete a category for authenticated user"""
    try:
        cs.delete_category(g.db, category_id, g.user_id)
        return jsonify({"message": "Category deleted successfully"}), 200
    except NotFoundError as ne:
        return jsonify({"error": str(ne)}), 404
    except Exception as e:
        print(f"CategoryRoutes: Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500
