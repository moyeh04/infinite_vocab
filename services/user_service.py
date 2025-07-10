"""User Service - business logic for user operations."""

import logging

from data_access import user_dal as u_dal
from factories import UserFactory
from models import User
from schemas import UserCreateSchema, UserUpdateSchema
from utils import DatabaseError, NotFoundError, UserServiceError, generate_random_code

logger = logging.getLogger("infinite_vocab_app")


def get_or_create_user(db, user_id: str, schema: UserCreateSchema) -> tuple[User, bool]:
    """
    Retrieves a user if they exist, otherwise creates a new one.
    If an existing user is missing a user_code, it will be generated and saved.
    """
    logger.info(f"SERVICE: get_or_create_user invoked for user_id: {user_id}.")
    try:
        existing_user = u_dal.get_user_by_id(db, user_id)
        if existing_user:
            logger.info(f"SERVICE: Found existing user with ID '{user_id}'.")

            # If the user exists but is missing a code, generate and save one.
            if not existing_user.user_code:
                logger.warning(
                    f"SERVICE: User {user_id} is missing a user_code. Generating a new one."
                )
                new_code = generate_random_code()
                updated_user = u_dal.update_user(db, user_id, {"user_code": new_code})
                return updated_user, False  # Return updated user, was_created = False

            return existing_user, False  # Return original user, was_created = False

        logger.info(f"SERVICE: No user found for ID '{user_id}'. Creating new user.")
        new_user_model = UserFactory.create_from_schema(schema, user_id)
        created_user = u_dal.create_user(db, new_user_model)
        return created_user, True

    except DatabaseError as e:
        logger.error(f"SERVICE: DatabaseError in get_or_create_user for {user_id}: {e}")
        raise UserServiceError("Database operation failed.") from e


def get_user_profile(db, user_id: str) -> User:
    """Retrieves a user's profile by their ID."""

    logger.info(f"SERVICE: get_user_profile invoked for user_id: {user_id}.")
    try:
        user = u_dal.get_user_by_id(db, user_id)
        if not user:
            raise NotFoundError(f"User with ID '{user_id}' not found.")

        return user
    except DatabaseError as e:
        logger.error(f"SERVICE: DatabaseError in get_user_profile for {user_id}: {e}")
        raise UserServiceError("Failed to retrieve user profile.") from e


def update_user_profile(db, user_id: str, schema: UserUpdateSchema) -> User:
    """Updates a user's profile information."""

    logger.info(f"SERVICE: update_user_profile invoked for user_id: {user_id}.")
    try:
        updates = UserFactory.create_update_dict(schema)
        if not updates:
            logger.info(
                f"SERVICE: No fields to update for user {user_id}. Returning current profile."
            )
            return get_user_profile(db, user_id)

        updated_user = u_dal.update_user(db, user_id, updates)
        if not updated_user:
            raise NotFoundError(f"User with ID '{user_id}' not found for update.")

        logger.info(f"SERVICE: Successfully updated profile for user {user_id}.")
        return updated_user
    except (DatabaseError, NotFoundError) as e:
        logger.error(f"SERVICE: Error updating profile for user {user_id}: {e}")
        raise UserServiceError("Failed to update user profile.") from e
