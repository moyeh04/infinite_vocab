"""Category Data Access Layer"""

from typing import List, Optional

from models import Category
from utils import DatabaseError


def create_category(db, category: Category) -> Category:
    """Save category and return with ID and timestamp."""
    try:
        category_data = {
            "user_id": category.user_id,
            "category_name": category.category_name,
            "category_color": category.category_color,
            "createdAt": db.SERVER_TIMESTAMP,
        }

        # Firestore .add() returns (timestamp, doc_ref) tuple
        # We need the doc_ref to get the generated ID
        doc_ref = db.collection("categories").add(category_data)[1]
        saved_doc = doc_ref.get()
        saved_data = saved_doc.to_dict()

        return Category(
            category_id=doc_ref.id,
            category_name=saved_data["category_name"],
            category_color=saved_data["category_color"],
            user_id=saved_data["user_id"],
            created_at=saved_data["createdAt"],
        )
    except Exception as e:
        raise DatabaseError(f"Failed to create category: {str(e)}")


def get_categories_by_user(db, user_id: str) -> List[Category]:
    """Get all categories for user."""
    try:
        query = (
            db.collection("categories")
            .where("user_id", "==", user_id)
            .order_by("category_name")
        )
        docs = query.stream()

        categories = []
        for doc in docs:
            data = doc.to_dict()
            category = Category(
                category_id=doc.id,
                category_name=data["category_name"],
                category_color=data["category_color"],
                user_id=data["user_id"],
                created_at=data.get("createdAt"),
            )
            categories.append(category)
        return categories
    except Exception as e:
        raise DatabaseError(f"Failed to get categories: {str(e)}")


def get_category_by_id(db, category_id: str) -> Optional[Category]:
    """Get category by ID."""
    try:
        doc = db.collection("categories").document(category_id).get()
        if not doc.exists:
            return None

        data = doc.to_dict()
        return Category(
            category_id=doc.id,
            category_name=data["category_name"],
            category_color=data["category_color"],
            user_id=data["user_id"],
            created_at=data.get("createdAt"),
        )
    except Exception as e:
        raise DatabaseError(f"Failed to get category: {str(e)}")


def update_category(db, category_id: str, updates: dict) -> Optional[Category]:
    """Update category fields."""
    try:
        doc_ref = db.collection("categories").document(category_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        updates["updatedAt"] = db.SERVER_TIMESTAMP
        doc_ref.update(updates)

        updated_doc = doc_ref.get()
        data = updated_doc.to_dict()

        return Category(
            category_id=doc_ref.id,
            category_name=data["category_name"],
            category_color=data["category_color"],
            user_id=data["user_id"],
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
        )
    except Exception as e:
        raise DatabaseError(f"Failed to update category: {str(e)}")


def delete_category(db, category_id: str) -> bool:
    """Delete category by ID."""
    try:
        doc_ref = db.collection("categories").document(category_id)
        doc = doc_ref.get()

        if not doc.exists:
            return False

        doc_ref.delete()
        return True
    except Exception as e:
        raise DatabaseError(f"Failed to delete category: {str(e)}")
