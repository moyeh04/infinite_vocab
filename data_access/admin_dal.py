"""Admin Data Access Layer"""

from firebase_admin import firestore

from utils import DatabaseError


def get_all_admin_ids(db) -> set:
    """Retrieves a set of all user IDs that are admins for quick lookups."""
    try:
        admin_ids = set()
        docs = db.collection("admins").stream()
        for doc in docs:
            admin_ids.add(doc.id)
        return admin_ids

    except Exception as e:
        raise DatabaseError(f"Failed to get all admin IDs: {e}") from e


def promote_user_to_admin(db, user_id_to_promote: str, assigning_admin_id: str) -> bool:
    """Creates a new document in the 'admins' collection to grant admin privileges."""
    try:
        doc_ref = db.collection("admins").document(user_id_to_promote)
        doc_ref.set(
            {
                "role": "admin",
                "assignedBy": assigning_admin_id,
                "assignedAt": firestore.SERVER_TIMESTAMP,
            }
        )
        return True
    except Exception as e:
        raise DatabaseError(f"Failed to promote user {user_id_to_promote}: {e}") from e


def update_admin_role(db, user_id: str, new_role: str) -> bool:
    """Updates the role field for an existing admin document."""

    try:
        doc_ref = db.collection("admins").document(user_id)
        doc_ref.update({"role": new_role, "updatedAt": firestore.SERVER_TIMESTAMP})
        return True
    except Exception as e:
        raise DatabaseError(f"Failed to update role for admin {user_id}: {e}") from e


def demote_admin(db, user_id_to_demote: str) -> bool:
    """Deletes an admin document, revoking admin privileges."""

    try:
        db.collection("admins").document(user_id_to_demote).delete()
        return True
    except Exception as e:
        raise DatabaseError(f"Failed to demote admin {user_id_to_demote}: {e}") from e
