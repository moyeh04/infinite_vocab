"""User Service - business logic for user operations."""

from data_access import user_dal as u_dal
from factories import UserFactory
from models import User
from schemas import UserCreateSchema, UserUpdateSchema
from utils import DatabaseError, NotFoundError, UserServiceError


def get_or_create_user(db, user_id: str, schema: UserCreateSchema) -> tuple[User, bool]:
    """
    Retrieves a user if they exist, otherwise creates a new one.
    Returns a tuple containing the User model and a boolean indicating if the user was newly created.
    """
    try:
        # 1. Check if the user already exists in the database.
        existing_user = u_dal.get_user_by_id(db, user_id)
        if existing_user:
            print(f"SERVICE: Found existing user with ID '{user_id}'.")
            return existing_user, False  # Return user, was_created = False

        # 2. If user doesn't exist, use the factory to create a new User model.
        print(f"SERVICE: No user found for ID '{user_id}'. Creating new user.")
        new_user_model = UserFactory.create_from_schema(schema, user_id)

        # 3. Pass the new model to the DAL to save it in Firestore.
        created_user = u_dal.create_user(db, new_user_model)
        return created_user, True  # Return user, was_created = True

    except DatabaseError as e:
        # Wrap lower-level errors in a service-specific exception
        raise UserServiceError("Database operation failed.") from e


def get_user_profile(db, user_id: str) -> User:
    """Retrieves a user's profile by their ID."""
    try:
        user = u_dal.get_user_by_id(db, user_id)
        if not user:
            # This case should be rare if the user is authenticated, but is good practice.
            raise NotFoundError(f"User with ID '{user_id}' not found.")
        return user
    except DatabaseError as e:
        raise UserServiceError("Failed to retrieve user profile.") from e


def update_user_profile(db, user_id: str, schema: UserUpdateSchema) -> User:
    """Updates a user's profile information."""
    try:
        # 1. Use the factory to create a dictionary of fields to update.
        # This filters out any fields that were not provided in the request.
        updates = UserFactory.create_update_dict(schema)

        if not updates:
            # If no actual data was sent, just return the current user profile.
            return get_user_profile(db, user_id)

        # 2. Pass the updates to the DAL.
        updated_user = u_dal.update_user(db, user_id, updates)
        if not updated_user:
            raise NotFoundError(f"User with ID '{user_id}' not found for update.")

        return updated_user
    except (DatabaseError, NotFoundError) as e:
        raise UserServiceError("Failed to update user profile.") from e
