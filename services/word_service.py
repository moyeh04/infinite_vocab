from firebase_admin import firestore

from data_access import word_dal as wd
from utils.exceptions import (
    DatabaseError,
    DuplicateEntryError,
    ForbiddenError,
    NotFoundError,
    WordServiceError,
)


def _get_word_existence_details(db, user_id: str, word_text: str) -> dict:
    """
    Checks if a word with the given text exists for the user.
    Returns a dictionary: {"exists": True/False, "word_id": id_or_None}
    Raises WordServiceError if the underlying DAL call fails.
    """
    try:
        snapshots = wd.find_word_by_text_for_user(db, user_id, word_text)

        if snapshots:
            return {"exists": True, "word_id": snapshots[0].id}
        else:
            return {"exists": False, "word_id": None}
    except DatabaseError as de:
        print(
            f"WordService (helper): DatabaseError during existence check for word '{word_text}', user '{user_id}': {str(de)}"
        )
        raise WordServiceError(
            f"Could not check existence for word '{word_text}' due to a database issue."
        ) from de
    except Exception as e:
        print(
            f"WordService (helper): Unexpected error during existence check for word '{word_text}', user '{user_id}': {str(e)}"
        )
        raise WordServiceError(
            f"An unexpected error occurred while checking existence for word '{word_text}'."
        ) from e


def _get_and_verify_word_ownership(
    db, current_user_id: str, target_word_id: str
) -> dict:
    """
    Internal helper to fetch a word by ID, check existence, and verify ownership.
    Returns the word's data dictionary if valid and owned.
    Raises NotFoundError or ForbiddenError if checks fail.
    Raises WordServiceError for underlying database issues.

    Note: We use this helper in multiple contexts - sometimes we need the returned
    word data (like in get_word_details_for_user), and sometimes we just need the
    validation to pass without using the data (like in add_description_for_user).
    Both use cases are intentional and valid.
    """
    try:
        snapshot = wd.get_word_by_id(db, target_word_id)

        if not snapshot.exists:
            raise NotFoundError(f"Word with ID '{target_word_id}' not found.")
        word_data = snapshot.to_dict()

        if word_data.get("user_id") != current_user_id:  # Ownership check
            raise NotFoundError(
                f"Word with ID '{target_word_id}' not found or not accessible."
            )

        word_data["id"] = snapshot.id
        return word_data
    except NotFoundError:
        raise
    except DatabaseError as de:
        print(
            f"WordService (helper): DatabaseError for word_id '{target_word_id}', user '{current_user_id}': {str(de)}"
        )
        raise WordServiceError(
            "Could not retrieve word due to a data access issue."
        ) from de
    except Exception as e:
        print(
            f"WordService (helper): Unexpected error for word_id '{target_word_id}', user '{current_user_id}': {str(e)}"
        )
        raise WordServiceError(
            "An unexpected service error occurred while verifying word."
        ) from e


def create_word_for_user(
    db,
    user_id: str,
    word_text_to_add: str,
    initial_description: str,
    initial_example: str,
) -> dict:
    """
    Creates a new word for the user if it doesn't already exist.
    Adds initial description and example.
    Returns a dictionary of the created word's details.
    Raises DuplicateEntryError if word already exists.
    Raises WordServiceError for other issues.
    """
    try:
        existence_details = _get_word_existence_details(db, user_id, word_text_to_add)

        if existence_details["exists"]:
            existing_doc_id = existence_details["word_id"]
            print(
                f"WordService: Duplicate found: Word '{word_text_to_add}' for user '{user_id}' (ID: {existing_doc_id})."
            )
            raise DuplicateEntryError(
                f"Word '{word_text_to_add}' already exists in your list. Try adding a star to the existing entry instead?",
                conflicting_id=existing_doc_id,
            )

        data_to_save = {
            "word": word_text_to_add,
            "descriptions": [initial_description],
            "examples": [initial_example],
            "stars": 0,
            "user_id": user_id,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
        }

        _timestamp, new_word_ref = wd.add_word_to_db(db, data_to_save)

        print(
            f"WordService: Word '{word_text_to_add}' added with ID: {new_word_ref.id} for user '{user_id}'."
        )
        response_data = data_to_save.copy()
        response_data["word_id"] = new_word_ref.id
        # Remove createdAt/updatedAt fields because they hold SERVER_TIMESTAMP
        # sentinels which cannot be directly converted to JSON by jsonify.
        del response_data["createdAt"]
        del response_data["updatedAt"]

        return response_data
    except DuplicateEntryError:
        raise
    except WordServiceError:
        raise
    except DatabaseError as de:
        print(
            f"WordService: Unwrapped DatabaseError in create_word_for_user for '{word_text_to_add}', UID '{user_id}': {str(de)}"
        )
        raise WordServiceError(
            "A database problem occurred while creating your word."
        ) from de
    except Exception as e:
        print(
            f"WordService: Unexpected error in create_word_for_user for '{word_text_to_add}', UID '{user_id}': {str(e)}"
        )
        raise WordServiceError(
            "An unexpected error occurred in the word service while creating your word."
        ) from e


def check_word_exists(db, user_id: str, word_text: str) -> dict:
    """
    Checks if a word exists for a user and returns its status and ID if found.
    This service function calls the internal helper.
    """
    try:
        existence_details = _get_word_existence_details(db, user_id, word_text)
        return existence_details
    except WordServiceError:
        raise
    except Exception as e:
        print(
            f"WordService: Unexpected error in check_word_exists_service for word '{word_text}', UID '{user_id}': {str(e)}"
        )
        raise WordServiceError(
            "An unexpected error occurred while checking word existence."
        ) from e


def list_words_for_user(db, user_id):
    try:
        word_snapshots = wd.get_all_words_for_user_sorted_by_stars(db, user_id)
        results_list = []
        for document_snapshot in word_snapshots:
            word_data = document_snapshot.to_dict()
            word_data["word_id"] = document_snapshot.id
            results_list.append(word_data)

        print(
            f"WordService: Prepared results_list with {len(results_list)} items for user {user_id}."
        )
        # print(f"WordService: Full results_list: {results_list} for user {user_id}.") # Optional: very verbose for many words
        return results_list
    except DatabaseError as de:
        print(
            f"WordService: DatabaseError encountered while listing words for user {user_id}: {str(de)}"
        )
        raise WordServiceError(
            "A database problem occurred while fetching your words."
        ) from de
    except Exception as e:
        print(
            f"WordService: Unexpected error in list_words_for_user for user {user_id}: {str(e)}"
        )
        raise WordServiceError(
            "An unexpected service error occurred while fetching your words."
        ) from e


def add_description_for_user(
    db, current_user_id: str, word_id: str, description_text: str
):
    """
    Adds a description to an existing word, after verifying ownership.
    """
    try:
        # We don't need the word data here, because we are going to add a description, not getting word details.
        # The function will automatically raise an error if the word doesn't exist or the user doesn't own it.
        _ = _get_and_verify_word_ownership(db, current_user_id, word_id)
        # If this check passes then we can add the description.
        wd.append_description_to_word_db(db, word_id, description_text)

        return {
            "message": f"Description '{description_text}' added successfully.",
            "word_id": word_id,
        }
    except NotFoundError:
        raise
    except DatabaseError as de:
        print(
            f"WordService: DatabaseError adding description to word '{word_id}': {str(de)}"
        )
        raise WordServiceError(
            "Could not add description due to a data access issue."
        ) from de
    except Exception as e:
        print(
            f"WordService: Unexpected error adding description to word '{word_id}': {str(e)}"
        )
        raise WordServiceError(
            "An unexpected service error occurred while adding description."
        ) from e


def add_example_for_user(db, current_user_id: str, word_id: str, example_text: str):
    """
    Adds an example to an existing word, after verifying ownership.
    """
    try:
        _ = _get_and_verify_word_ownership(db, current_user_id, word_id)
        wd.append_example_to_word_db(db, word_id, example_text)

        return {
            "message": f"Example '{example_text}' added successfully.",
            "word_id": word_id,
        }
    except NotFoundError:
        raise
    except DatabaseError as de:
        print(
            f"WordService: DatabaseError adding example to word '{word_id}': {str(de)}"
        )
        raise WordServiceError(
            "Could not add example due to a data access issue."
        ) from de
    except Exception as e:
        print(
            f"WordService: Unexpected error adding example to word '{word_id}': {str(e)}"
        )
        raise WordServiceError(
            "An unexpected service error occurred while adding example."
        ) from e


def get_word_details_for_user(db, current_user_id: str, target_word_id: str) -> dict:
    """
    Fetches details for a specific word if it exists and belongs to the user.
    """
    word_data_with_id = _get_and_verify_word_ownership(
        db, current_user_id, target_word_id
    )
    return word_data_with_id


def star_word_for_user(db, user_id, word_id):
    try:
        transaction = db.transaction()
        atomic_result = wd.atomic_update(transaction, db, word_id, user_id)

        if atomic_result == "NOT_FOUND":
            raise NotFoundError(f"Word with ID '{word_id}' not found.")
        elif atomic_result == "FORBIDDEN":
            raise ForbiddenError("You are not authorized to modify this word.")

        new_star_count, word_text = atomic_result

        prompt_for_description = False
        prompt_for_example = False

        description_milestones = [5, 10, 15, 20]
        example_milestones = [10, 20, 30, 40]

        if new_star_count in description_milestones:
            prompt_for_description = True

        if new_star_count in example_milestones:
            prompt_for_example = True

        print(
            f"STAR_WORD: Star updated for word ID '{word_id}' (text: '{word_text}') for UID: {user_id}. New stars: {new_star_count}"
        )
        return {
            "message": f"Successfully starred word '{word_text}'.",
            "word_id": word_id,
            "new_star_count": new_star_count,
            "prompt_for_description": prompt_for_description,
            "prompt_for_example": prompt_for_example,
        }
    except (NotFoundError, ForbiddenError):
        raise
    except DatabaseError as de:
        print(
            f"WordService: DatabaseError starring word ID '{word_id}' (text: '{word_text}'): {str(de)}"
        )
        raise WordServiceError(
            "A database problem occurred while starring the word."
        ) from de
    except Exception as e:
        print(
            f"WordService: Unexpected error starring word ID '{word_id}' (text: '{word_text}'): {str(e)}"
        )
        raise WordServiceError(
            "An unexpected service error occurred while starring the word."
        ) from e
