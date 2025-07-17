"""Example service - Clean CRUD operations following category service pattern"""

import logging

from data_access import word_dal as w_dal
from factories import WordFactory
from models import Example
from schemas import ExampleCreateSchema, ExampleUpdateSchema
from utils import DatabaseError, NotFoundError, WordServiceError
from firebase_admin import firestore

logger = logging.getLogger("infinite_vocab_app")


def _get_example_by_id_with_ownership(
    db, user_id: str, word_id: str, example_id: str
) -> Example:
    """Helper to get example with ownership validation - like get_category_by_id pattern"""
    # First verify word ownership using word service
    from .word_service import get_word_details_for_user

    get_word_details_for_user(db, user_id, word_id)  # This handles word ownership

    # Then get the example
    example = w_dal.get_example_by_id(
        db, word_id, example_id
    )  # DAL returns Example model now!
    if not example:
        raise NotFoundError(
            f"Example with ID '{example_id}' not found in word '{word_id}'."
        )
    if example.user_id != user_id:  # Simple property access like category
        logger.warning(
            f"SERVICE: Ownership check failed for example '{example_id}'. Requester: '{user_id}', Owner: '{example.user_id}'."
        )
        raise NotFoundError(
            f"Example with ID '{example_id}' not found or not accessible."
        )
    return example


def add_example_for_user(
    db,
    user_id: str,
    word_id: str,
    schema: ExampleCreateSchema,
    initial_example: bool = False,
) -> dict:
    """Adds an example to a word - like create_category pattern"""
    logger.info(
        f"SERVICE: add_example_for_user invoked for word '{word_id}' by user '{user_id}'."
    )
    try:
        # Verify word ownership first (reuse word service)
        from .word_service import get_word_details_for_user

        get_word_details_for_user(
            db, user_id, word_id
        )  # This handles ownership validation

        # Create example model using factory - like category
        example_model = WordFactory.create_example_from_schema(
            schema, user_id, is_initial=initial_example
        )

        # Prepare data for database
        example_data = {
            "example_text": example_model.example_text,
            "word_id": word_id,
            "is_initial": example_model.is_initial,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
            "user_id": example_model.user_id,
        }

        # Add to database
        new_example_ref = w_dal.append_example_to_word_db(db, word_id, example_data)
        new_example_id = new_example_ref.id

        logger.info(
            f"SERVICE: Successfully added example to word '{word_id}' for user '{user_id}'."
        )
        return {
            "message": f"Example added successfully to word '{word_id}'.",
            "word_id": word_id,
            "example_id": new_example_id,
        }

    except NotFoundError:
        raise
    except DatabaseError as e:
        logger.error(
            f"SERVICE: DatabaseError during example creation for word '{word_id}': {e}",
            exc_info=True,
        )
        raise WordServiceError("Could not add example due to a database issue.") from e
    except Exception as e:
        logger.error(
            f"SERVICE: Unexpected error during example creation for word '{word_id}': {e}",
            exc_info=True,
        )
        raise WordServiceError(
            "An unexpected service error occurred while adding example."
        ) from e


def update_example_for_user(
    db, user_id: str, word_id: str, example_id: str, example_text: str
) -> dict:
    """Updates an example - like update_category pattern"""
    logger.info(
        f"SERVICE: update_example_for_user invoked for example '{example_id}' by user '{user_id}'."
    )
    try:
        # Get existing example with ownership validation (reuse helper)
        existing_example = _get_example_by_id_with_ownership(
            db, user_id, word_id, example_id
        )

        old_example_text = existing_example.example_text

        # Update the example using DAL
        w_dal.update_example_to_word_db(db, word_id, example_id, example_text)

        logger.info(
            f"SERVICE: Successfully updated example '{example_id}' for user '{user_id}'."
        )
        return {
            "message": f"Example '{old_example_text}' successfully updated to '{example_text}'.",
            "word_id": word_id,
            "example_id": example_id,
        }

    except NotFoundError:
        raise
    except DatabaseError as e:
        logger.error(
            f"SERVICE: DatabaseError during example update for '{example_id}': {e}",
            exc_info=True,
        )
        raise WordServiceError(
            "Could not update example due to a database issue."
        ) from e
    except Exception as e:
        logger.error(
            f"SERVICE: Unexpected error during example update for '{example_id}': {e}",
            exc_info=True,
        )
        raise WordServiceError(
            "An unexpected service error occurred while updating example."
        ) from e


def delete_example_for_user(db, user_id: str, word_id: str, example_id: str) -> dict:
    """Deletes an example - like delete_category pattern"""
    logger.info(
        f"SERVICE: delete_example_for_user invoked for example '{example_id}' by user '{user_id}'."
    )
    try:
        # Verify ownership first (reuse helper)
        _get_example_by_id_with_ownership(db, user_id, word_id, example_id)

        # Delete the example using DAL
        w_dal.delete_example_from_word_db(db, word_id, example_id)

        logger.info(
            f"SERVICE: Successfully deleted example '{example_id}' for user '{user_id}'."
        )
        return {
            "message": f"Example deleted successfully from word '{word_id}'.",
            "word_id": word_id,
            "example_id": example_id,
        }

    except NotFoundError:
        raise
    except DatabaseError as e:
        logger.error(
            f"SERVICE: DatabaseError during example deletion for '{example_id}': {e}",
            exc_info=True,
        )
        raise WordServiceError(
            "Could not delete example due to a database issue."
        ) from e
    except Exception as e:
        logger.error(
            f"SERVICE: Unexpected error during example deletion for '{example_id}': {e}",
            exc_info=True,
        )
        raise WordServiceError(
            "An unexpected service error occurred while deleting example."
        ) from e
