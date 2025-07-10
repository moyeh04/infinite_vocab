"""
DAL for managing the relationship between admins and students (users).

This layer interacts with the 'admin_student_relations' collection.
"""

import logging
from typing import List, Optional

from utils import DatabaseError

logger = logging.getLogger("infinite_vocab_app")


def create_link(db, admin_id: str, student_id: str) -> bool:
    """Creates a document to link an admin to a student."""

    link_id = f"{admin_id}_{student_id}"
    logger.info(f"DAL: Creating admin-student link with ID: {link_id}")
    try:
        doc_ref = db.collection("admin_student_relations").document(link_id)
        doc_ref.set({"admin_id": admin_id, "student_id": student_id})
        return True
    except Exception as e:
        logger.error(
            f"DAL: Failed to create admin-student link for admin {admin_id}, student {student_id}: {e}"
        )
        raise DatabaseError("Failed to create admin-student link.") from e


def remove_link(db, admin_id: str, student_id: str) -> bool:
    """Removes the link between an admin and a student."""
    link_id = f"{admin_id}_{student_id}"
    logger.info(f"DAL: Removing admin-student link with ID: {link_id}")
    try:
        doc_ref = db.collection("admin_student_relations").document(link_id)
        if not doc_ref.get().exists:
            logger.warning(
                f"DAL: Attempted to remove a non-existent link with ID: {link_id}"
            )
            return False
        doc_ref.delete()
        return True
    except Exception as e:
        logger.error(
            f"DAL: Failed to remove admin-student link for admin {admin_id}, student {student_id}: {e}"
        )
        raise DatabaseError("Failed to remove admin-student link.") from e


def get_link_by_student_id(db, student_id: str) -> Optional[dict]:
    """
    Finds if a student is already assigned to any admin.
    Returns the link document data if found, otherwise None.
    """
    logger.info(
        f"DAL: Checking if student {student_id} is already assigned to an admin."
    )
    try:
        query = (
            db.collection("admin_student_relations")
            .where("student_id", "==", student_id)
            .limit(1)
        )
        docs = list(query.stream())
        if not docs:
            return None

        logger.info(f"DAL: Found existing link for student {student_id}.")
        return docs[0].to_dict()
    except Exception as e:
        logger.error(
            f"DAL: Failed to query for student link for student_id {student_id}: {e}"
        )
        raise DatabaseError("Failed to check for existing student link.") from e


def get_students_for_admin(db, admin_id: str) -> List[str]:
    """Retrieves a list of all student_ids assigned to a specific admin."""
    logger.info(f"DAL: Getting all students for admin_id: {admin_id}")
    try:
        student_ids = []
        query = db.collection("admin_student_relations").where(
            "admin_id", "==", admin_id
        )
        docs = query.stream()
        for doc in docs:
            student_ids.append(doc.to_dict().get("student_id"))

        logger.info(f"DAL: Found {len(student_ids)} students for admin {admin_id}.")
        return student_ids
    except Exception as e:
        logger.error(f"DAL: Failed to get students for admin {admin_id}: {e}")
        raise DatabaseError("Failed to retrieve students for admin.") from e
