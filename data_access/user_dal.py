"""User Data Access Layer"""

import logging
from typing import Optional

from firebase_admin import firestore

from models import User
from utils import DatabaseError

logger = logging.getLogger("infinite_vocab_app")


def create_user(db, user: User) -> User:
    """Saves a new user to Firestore and returns the created user."""

    logger.info(f"DAL: Creating user document for user_id: {user.user_id}")
    try:
        user_data = {
            "user_name": user.user_name,
            "user_code": user.user_code,
            "total_score": user.total_score,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
        }
        doc_ref = db.collection("users").document(user.user_id)
        doc_ref.set(user_data)

        created_doc = doc_ref.get()
        logger.info(
            f"DAL: Successfully created user document with ID: {created_doc.id}"
        )

        # Re-create the model from the DB data to include server-side timestamps
        db_data = created_doc.to_dict()
        db_data["user_id"] = created_doc.id
        return User.model_validate(db_data)

    except Exception as e:
        logger.error(f"DAL: Failed to create user {user.user_id}: {e}")
        raise DatabaseError(f"Failed to create user: {e}") from e


def get_user_by_id(db, user_id: str) -> Optional[User]:
    """Gets a user from Firestore by their document ID."""
    logger.info(f"DAL: Getting user document for user_id: {user_id}")
    try:
        doc_ref = db.collection("users").document(user_id)
        doc = doc_ref.get()

        if not doc.exists:
            logger.warning(f"DAL: User document not found for user_id: {user_id}")
            return None

        # Unpack the dictionary from Firestore and add the document ID
        db_data = doc.to_dict()
        db_data["user_id"] = doc.id
        return User.model_validate(db_data)

    except Exception as e:
        logger.error(f"DAL: Failed to get user by ID {user_id}: {e}")
        raise DatabaseError(f"Failed to get user by ID: {e}") from e


def update_user(db, user_id: str, updates: dict) -> Optional[User]:
    """Updates a user document in Firestore."""
    logger.info(
        f"DAL: Updating user document for user_id: {user_id} with keys {list(updates.keys())}"
    )
    try:
        doc_ref = db.collection("users").document(user_id)
        doc = doc_ref.get()

        if not doc.exists:
            logger.warning(
                f"DAL: User document not found for update for user_id: {user_id}"
            )
            return None

        updates["updatedAt"] = firestore.SERVER_TIMESTAMP
        doc_ref.update(updates)

        updated_doc = doc_ref.get()
        logger.info(f"DAL: Successfully updated user document for user_id: {user_id}")
        db_data = updated_doc.to_dict()
        db_data["user_id"] = updated_doc.id
        return User.model_validate(db_data)

    except Exception as e:
        logger.error(f"DAL: Failed to update user {user_id}: {e}")
        raise DatabaseError(f"Failed to update user: {e}") from e


def list_all_users(db) -> list[User]:
    """Retrieves all user documents from the users collection."""

    logger.info("DAL: Listing all user documents.")
    try:
        users = []

        docs = db.collection("users").stream()
        for doc in docs:
            db_data = doc.to_dict()
            db_data["user_id"] = doc.id
            users.append(User.model_validate(db_data))
        logger.info(f"DAL: Retrieved {len(users)} total users.")
        return users

    except Exception as e:
        logger.error(f"DAL: Failed to list all users: {e}")
        raise DatabaseError(f"Failed to list all users: {e}") from e
