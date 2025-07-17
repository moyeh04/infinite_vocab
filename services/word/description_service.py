"""Description service - Clean CRUD operations following category service pattern"""

import logging

from data_access import word_dal as w_dal
from factories import WordFactory
from models import Description
from schemas import DescriptionCreateSchema, DescriptionUpdateSchema
from utils import DatabaseError, NotFoundError, WordServiceError
from firebase_admin import firestore

logger = logging.getLogger("infinite_vocab_app")


def _get_description_by_id_with_ownership(
    db, user_id: str, word_id: str, description_id: str
) -> Description:
    """Helper to get description with ownership validation - like get_category_by_id pattern"""
    # First verify word ownership using word service
    from .word_service import get_word_details_for_user

    get_word_details_for_user(db, user_id, word_id)  # This handles word ownership

    # Then get the description
    description = w_dal.get_description_by_id(
        db, word_id, description_id
    )  # DAL returns Description model now!
    if not description:
        raise NotFoundError(
            f"Description with ID '{description_id}' not found in word '{word_id}'."
        )
    if description.user_id != user_id:  # Simple property access like category
        logger.warning(
            f"SERVICE: Ownership check failed for description '{description_id}'. Requester: '{user_id}', Owner: '{description.user_id}'."
        )
        raise NotFoundError(
            f"Description with ID '{description_id}' not found or not accessible."
        )
    return description


def add_description_for_user(
    db,
    user_id: str,
    word_id: str,
    schema: DescriptionCreateSchema,
    initial_description: bool = False,
) -> dict:
    """Adds a description to a word - like create_category pattern"""
    logger.info(
        f"SERVICE: add_description_for_user invoked for word '{word_id}' by user '{user_id}'."
    )
    try:
        # Verify word ownership first (reuse word service)
        from .word_service import get_word_details_for_user

        get_word_details_for_user(
            db, user_id, word_id
        )  # This handles ownership validation

        # Create description model using factory - like category
        description_model = WordFactory.create_description_from_schema(
            schema, user_id, is_initial=initial_description
        )

        # Prepare data for database
        description_data = {
            "description_text": description_model.description_text,
            "word_id": word_id,
            "is_initial": description_model.is_initial,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
            "user_id": description_model.user_id,
        }

        # Add to database
        new_description_ref = w_dal.append_description_to_word_db(
            db, word_id, description_data
        )
        new_description_id = new_description_ref.id

        logger.info(
            f"SERVICE: Successfully added description to word '{word_id}' for user '{user_id}'."
        )
        return {
            "message": f"Description added successfully to word '{word_id}'.",
            "word_id": word_id,
            "description_id": new_description_id,
        }

    except NotFoundError:
        raise
    except DatabaseError as e:
        logger.error(
            f"SERVICE: DatabaseError during description creation for word '{word_id}': {e}",
            exc_info=True,
        )
        raise WordServiceError(
            "Could not add description due to a database issue."
        ) from e
    except Exception as e:
        logger.error(
            f"SERVICE: Unexpected error during description creation for word '{word_id}': {e}",
            exc_info=True,
        )
        raise WordServiceError(
            "An unexpected service error occurred while adding description."
        ) from e


def update_description_for_user(
    db, user_id: str, word_id: str, description_id: str, description_text: str
) -> dict:
    """Updates a description - like update_category pattern"""
    logger.info(
        f"SERVICE: update_description_for_user invoked for description '{description_id}' by user '{user_id}'."
    )
    try:
        # Get existing description with ownership validation (reuse helper)
        existing_description = _get_description_by_id_with_ownership(
            db, user_id, word_id, description_id
        )

        old_description_text = existing_description.description_text

        # Update the description using DAL
        w_dal.update_description_to_word_db(
            db, word_id, description_id, description_text
        )

        logger.info(
            f"SERVICE: Successfully updated description '{description_id}' for user '{user_id}'."
        )
        return {
            "message": f"Description '{old_description_text}' successfully updated to '{description_text}'.",
            "word_id": word_id,
            "description_id": description_id,
        }

    except NotFoundError:
        raise
    except DatabaseError as e:
        logger.error(
            f"SERVICE: DatabaseError during description update for '{description_id}': {e}",
            exc_info=True,
        )
        raise WordServiceError(
            "Could not update description due to a database issue."
        ) from e
    except Exception as e:
        logger.error(
            f"SERVICE: Unexpected error during description update for '{description_id}': {e}",
            exc_info=True,
        )
        raise WordServiceError(
            "An unexpected service error occurred while updating description."
        ) from e


def delete_description_for_user(
    db, user_id: str, word_id: str, description_id: str
) -> dict:
    """Deletes a description - like delete_category pattern"""
    logger.info(
        f"SERVICE: delete_description_for_user invoked for description '{description_id}' by user '{user_id}'."
    )
    try:
        # Verify ownership first (reuse helper)
        _get_description_by_id_with_ownership(db, user_id, word_id, description_id)

        # Delete the description using DAL
        w_dal.delete_description_from_word_db(db, word_id, description_id)

        logger.info(
            f"SERVICE: Successfully deleted description '{description_id}' for user '{user_id}'."
        )
        return {
            "message": f"Description deleted successfully from word '{word_id}'.",
            "word_id": word_id,
            "description_id": description_id,
        }

    except NotFoundError:
        raise
    except DatabaseError as e:
        logger.error(
            f"SERVICE: DatabaseError during description deletion for '{description_id}': {e}",
            exc_info=True,
        )
        raise WordServiceError(
            "Could not delete description due to a database issue."
        ) from e
    except Exception as e:
        logger.error(
            f"SERVICE: Unexpected error during description deletion for '{description_id}': {e}",
            exc_info=True,
        )
        raise WordServiceError(
            "An unexpected service error occurred while deleting description."
        ) from e
