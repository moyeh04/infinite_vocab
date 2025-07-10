"""User Factory - Business Logic for User object creation."""

import logging

from models import User
from schemas import UserCreateSchema, UserUpdateSchema
from utils.helpers import generate_random_code

logger = logging.getLogger("infinite_vocab_app")


class UserFactory:
    """Factory for creating User objects with business rules."""

    @staticmethod
    def create_from_schema(schema: UserCreateSchema, user_id: str) -> User:
        """Create a new User model from a validated schema."""
        logger.info(f"FACTORY: Creating new user model for user_id: {user_id}")
        # Business Rule: A new user must be assigned a unique 8-character code.
        user_code = generate_random_code(8)
        logger.info(
            f"FACTORY: Generated user_code '{user_code}' for user_id: {user_id}"
        )

        # Construct the User model with all necessary initial data.
        return User(
            user_id=user_id,
            user_name=schema.user_name,
            user_code=user_code,
        )

    @staticmethod
    def create_update_dict(schema: UserUpdateSchema) -> dict:
        """Create an update dictionary from the update schema."""

        # This creates a dictionary containing only the fields that were
        # actually provided in the request, filtering out the `None` values.
        updates = schema.model_dump(exclude_unset=True)
        logger.info(
            f"FACTORY: Created update dictionary with keys: {list(updates.keys())}"
        )

        return updates
