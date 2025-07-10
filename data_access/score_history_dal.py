"""DAL for the total_score_history collection."""

import logging
from typing import List

from firebase_admin import firestore

from utils import DatabaseError

logger = logging.getLogger("infinite_vocab_app")


def create_score_history_entry(db, entry_data: dict) -> bool:
    """Creates a new document in the total_score_history collection."""
    logger.info(
        f"DAL: Creating score history entry for user {entry_data.get('user_id')}."
    )
    try:
        entry_data["createdAt"] = firestore.SERVER_TIMESTAMP
        db.collection("total_score_history").add(entry_data)
        return True
    except Exception as e:
        logger.error(f"DAL: Failed to create score history entry: {e}")
        raise DatabaseError("Failed to create score history entry.") from e


def get_history_for_user(db, user_id: str) -> List[dict]:
    """Retrieves all score history entries for a specific user, sorted by creation date."""
    logger.info(f"DAL: Getting score history for user_id: {user_id}")
    try:
        history_entries = []
        query = (
            db.collection("total_score_history")
            .where("user_id", "==", user_id)
            .order_by("createdAt", direction="DESCENDING")
        )
        docs = query.stream()
        for doc in docs:
            entry = doc.to_dict()
            entry["entry_id"] = doc.id
            history_entries.append(entry)

        logger.info(
            f"DAL: Found {len(history_entries)} score history entries for user {user_id}."
        )
        return history_entries
    except Exception as e:
        logger.error(f"DAL: Failed to get score history for user {user_id}: {e}")
        raise DatabaseError("Failed to retrieve score history.") from e
