"""Core word service - Clean CRUD operations following category service pattern"""

import logging
from typing import List

from data_access import word_dal as w_dal
from factories import WordFactory
from models import Word
from schemas import WordCreateSchema, WordUpdateSchema
from utils import DatabaseError, DuplicateEntryError, NotFoundError, WordServiceError

logger = logging.getLogger("infinite_vocab_app")


def get_word_details_for_user(db, user_id: str, word_id: str) -> Word:
    """Retrieves a word by ID with user ownership validation - like get_category_by_id"""
    logger.info(
        f"SERVICE: get_word_details_for_user invoked for word '{word_id}' by user '{user_id}'."
    )
    try:
        word = w_dal.get_word_by_id(db, word_id)  # DAL returns Word model now!
        if not word:
            raise NotFoundError(f"Word with ID '{word_id}' not found.")
        if word.user_id != user_id:  # Simple property access like category
            logger.warning(
                f"SERVICE: Ownership check failed for word '{word_id}'. Requester: '{user_id}', Owner: '{word.user_id}'."
            )
            raise NotFoundError(f"Word with ID '{word_id}' not found.")
        return word
    except DatabaseError as e:
        logger.error(
            f"SERVICE: DatabaseError during get_word_details_for_user for '{word_id}': {e}",
            exc_info=True,
        )
        raise WordServiceError(
            "Could not retrieve word due to a database issue."
        ) from e


def create_word_for_user(db, user_id: str, schema: WordCreateSchema) -> Word:
    """Creates a new word for a user with duplicate validation - like create_category"""
    logger.info(
        f"SERVICE: create_word_for_user invoked for user '{user_id}' with word '{schema.word_text}'."
    )
    try:
        # Check for duplicates using case-insensitive search
        existing_word_id = w_dal.find_word_by_text_for_user(
            db, user_id, schema.word_text
        )
        if existing_word_id:
            logger.warning(
                f"SERVICE: Duplicate found: Word '{schema.word_text}' for user '{user_id}' (ID: {existing_word_id})."
            )
            raise DuplicateEntryError(
                f"Word '{schema.word_text}' already exists in your list. Try adding a star to the existing entry instead?",
                conflicting_id=existing_word_id,
            )

        # Create Word model using factory - like category
        word_model = WordFactory.create_from_schema(schema, user_id)

        # Prepare data for the MAIN WORD document
        from firebase_admin import firestore

        word_document_data = {
            "word_text": word_model.word_text,
            "word_text_search": word_model.word_text_search,
            "word_stars": word_model.word_stars,
            "user_id": word_model.user_id,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
        }

        # Create the MAIN WORD document using the DAL
        _timestamp, new_word_ref = w_dal.add_word_to_db(db, word_document_data)
        created_word_id = new_word_ref.id

        logger.info(
            f"SERVICE: Word '{schema.word_text}' added with ID: {created_word_id} for user '{user_id}'."
        )

        # Create initial description using factory
        from schemas import DescriptionCreateSchema

        desc_schema = DescriptionCreateSchema(description_text=schema.description_text)
        initial_desc_model = WordFactory.create_description_from_schema(
            desc_schema, user_id, is_initial=True
        )

        initial_desc_data = {
            "description_text": initial_desc_model.description_text,
            "is_initial": initial_desc_model.is_initial,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "user_id": initial_desc_model.user_id,
        }
        w_dal.append_description_to_word_db(db, created_word_id, initial_desc_data)

        # Create initial example using factory
        from schemas import ExampleCreateSchema

        example_schema = ExampleCreateSchema(example_text=schema.example_text)
        initial_example_model = WordFactory.create_example_from_schema(
            example_schema, user_id, is_initial=True
        )

        initial_ex_data = {
            "example_text": initial_example_model.example_text,
            "is_initial": initial_example_model.is_initial,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "user_id": initial_example_model.user_id,
        }
        w_dal.append_example_to_word_db(db, created_word_id, initial_ex_data)

        # Fetch the created word with all subcollections
        word_model = w_dal.get_word_by_id(db, created_word_id)

        logger.info(
            f"SERVICE: Successfully created word '{schema.word_text}' for user '{user_id}'."
        )
        return word_model

    except DuplicateEntryError:
        raise
    except DatabaseError as e:
        logger.error(
            f"SERVICE: DatabaseError during word creation for user '{user_id}': {e}",
            exc_info=True,
        )
        raise WordServiceError(
            f"Could not create word '{schema.word_text}' due to a database issue."
        ) from e
    except Exception as e:
        logger.error(
            f"SERVICE: Unexpected error during word creation for user '{user_id}': {e}",
            exc_info=True,
        )
        raise


def update_word_for_user(
    db, user_id: str, word_id: str, schema: WordUpdateSchema
) -> Word:
    """Updates a word with user validation - like update_category"""
    logger.info(
        f"SERVICE: update_word_for_user invoked for word '{word_id}' by user '{user_id}'."
    )
    try:
        existing_word = get_word_details_for_user(
            db, user_id, word_id
        )  # Reuse ownership check!
        updates = WordFactory.create_word_update_dict(schema)
        if not updates:
            return existing_word

        # Update the word using DAL
        w_dal.update_word_by_id(db, word_id, schema.word_text)

        # Fetch the updated word
        updated_word = get_word_details_for_user(db, user_id, word_id)

        logger.info(f"SERVICE: Successfully updated word '{word_id}'.")
        return updated_word

    except (NotFoundError, WordServiceError):
        raise
    except DatabaseError as e:
        logger.error(
            f"SERVICE: DatabaseError during word update for '{word_id}': {e}",
            exc_info=True,
        )
        raise WordServiceError("Could not update word due to a database issue.") from e


def delete_word_for_user(db, user_id: str, word_id: str) -> dict:
    """Deletes a word with user ownership validation - like delete_category"""
    logger.info(
        f"SERVICE: delete_word_for_user invoked for word '{word_id}' by user '{user_id}'."
    )
    try:
        word_to_delete = get_word_details_for_user(
            db, user_id, word_id
        )  # Reuse ownership check!

        # Delete word using DAL
        w_dal.delete_word_by_id(db, word_id)

        return {
            "message": f"Word '{word_to_delete.word_text}' deleted successfully.",
            "word_id": word_id,
        }
    except (NotFoundError, WordServiceError):
        raise
    except DatabaseError as e:
        logger.error(
            f"SERVICE: DatabaseError during word deletion for '{word_id}': {e}",
            exc_info=True,
        )
        raise WordServiceError("Could not delete word due to a database issue.") from e


def list_words_for_user(db, user_id: str) -> List[Word]:
    """Retrieves all words for a user, sorted by stars - like get_categories_by_user"""
    logger.info(f"SERVICE: list_words_for_user invoked for user '{user_id}'.")
    try:
        words = w_dal.get_all_words_for_user_sorted_by_stars(
            db, user_id
        )  # DAL returns List[Word] now!
        return words
    except DatabaseError as e:
        logger.error(
            f"SERVICE: DatabaseError during word retrieval for user '{user_id}': {e}",
            exc_info=True,
        )
        raise WordServiceError(
            "Could not retrieve words due to a database issue."
        ) from e


def check_word_exists(db, user_id: str, word_text: str) -> dict:
    """Checks if a word exists for a user and returns its status"""
    logger.info(
        f"SERVICE: check_word_exists invoked for user '{user_id}' with word '{word_text}'."
    )
    try:
        existing_word_id = w_dal.find_word_by_text_for_user(db, user_id, word_text)
        if existing_word_id:
            return {"exists": True, "word_id": existing_word_id}
        else:
            return {"exists": False, "word_id": None}
    except DatabaseError as e:
        logger.error(
            f"SERVICE: DatabaseError during word existence check for '{word_text}': {e}",
            exc_info=True,
        )
        raise WordServiceError(
            f"Could not check existence for word '{word_text}' due to a database issue."
        ) from e
