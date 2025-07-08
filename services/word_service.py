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

    Important:
        This service helper centralizes the logic for calling the DAL to find a word by text
        and translating the DAL's raw snapshot result into a clear business-relevant status
        (existence and ID). It's used by other service functions like create_word_for_user
        and check_word_exists_service.
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
    db,
    user_id: str,
    word_id: str,
    fetch_subcollections: bool = False,  # For performance
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
        snapshot = wd.get_word_by_id(db, word_id)

        if not snapshot.exists:
            raise NotFoundError(f"Word with ID '{word_id}' not found.")
        word_data = snapshot.to_dict()

        if word_data.get("user_id") != user_id:  # Ownership check
            raise NotFoundError(
                f"Word with ID '{word_id}' not found or not accessible."
            )

        word_data["word_id"] = snapshot.id
        if fetch_subcollections:
            word_data["descriptions"] = wd.get_all_descriptions_for_word(db, word_id)
            word_data["examples"] = wd.get_all_examples_for_word(db, word_id)
        return word_data
    except NotFoundError:
        raise
    except DatabaseError as de:
        print(
            f"WordService (helper): DatabaseError for word_id '{word_id}', user '{user_id}': {str(de)}"
        )
        raise WordServiceError(
            "Could not retrieve word due to a data access issue."
        ) from de
    except Exception as e:
        print(
            f"WordService (helper): Unexpected error for word_id '{word_id}', user '{user_id}': {str(e)}"
        )
        raise WordServiceError(
            "An unexpected service error occurred while verifying word."
        ) from e


def create_word_for_user(
    db,
    user_id: str,
    word_text_to_add: str,
    initial_description_text: str,
    initial_example_text: str,
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

        # 1. Prepare data for the MAIN WORD document
        word_document_data = {
            "word_text": word_text_to_add,
            "word_stars": 0,
            "user_id": user_id,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
        }

        # 2. Create the MAIN WORD document using the DAL
        _timestamp, new_word_ref = wd.add_word_to_db(db, word_document_data)
        created_word_id = new_word_ref.id

        print(
            f"WordService: Word '{word_text_to_add}' added with ID: {created_word_id} for user '{user_id}'."
        )

        # 3. Add the initial description to its 'descriptions' subcollection
        initial_desc_data = {
            "description_text": initial_description_text,
            "is_initial": True,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "user_id": user_id,
        }
        new_desc_ref = wd.append_description_to_word_db(
            db, created_word_id, initial_desc_data
        )

        # Fetch the newly created description document
        initial_description_doc = new_desc_ref.get()
        initial_description_data_for_response = None
        if initial_description_doc.exists:
            initial_description_data_for_response = initial_description_doc.to_dict()
            initial_description_data_for_response["description_id"] = (
                initial_description_doc.id
            )

        # 4. Add the initial example to its 'examples' subcollection
        initial_ex_data = {
            "example_text": initial_example_text,
            "is_initial": True,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "user_id": user_id,
        }
        new_ex_ref = wd.append_example_to_word_db(db, created_word_id, initial_ex_data)

        # Fetch the newly created example document
        initial_example_doc = new_ex_ref.get()
        initial_example_data_for_response = None
        if initial_example_doc.exists:
            initial_example_data_for_response = initial_example_doc.to_dict()
            initial_example_data_for_response["example_id"] = initial_example_doc.id

        # 5. Fetch the newly created word document to get actual timestamp values
        created_word_doc = new_word_ref.get()
        created_word_data = created_word_doc.to_dict()

        # 6. Prepare the response data with actual timestamps
        response_data = {
            "word_id": created_word_id,
            "word_text": word_text_to_add,
            "word_stars": 0,
            "user_id": user_id,
            "createdAt": created_word_data.get("createdAt"),
            "updatedAt": created_word_data.get("updatedAt"),
            "descriptions": (
                [initial_description_data_for_response]
                if initial_description_data_for_response
                else []
            ),
            "examples": (
                [initial_example_data_for_response]
                if initial_example_data_for_response
                else []
            ),
        }
        return response_data
    except DuplicateEntryError:
        raise
    except WordServiceError:
        raise
    except DatabaseError as de:
        print(
            f"WordService: Unwrapped DatabaseError in create_word_for_user for '{word_text_to_add}', user_id '{user_id}': {str(de)}"
        )
        raise WordServiceError(
            "A database problem occurred while creating your word."
        ) from de
    except Exception as e:
        print(
            f"WordService: Unexpected error in create_word_for_user for '{word_text_to_add}', user_id '{user_id}': {str(e)}"
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
            f"WordService: Unexpected error in check_word_exists_service for word '{word_text}', user_id '{user_id}': {str(e)}"
        )
        raise WordServiceError(
            "An unexpected error occurred while checking word existence."
        ) from e


def edit_word_for_user(db, user_id: str, word_id: str, new_word_text: str) -> dict:
    """
    Updates the text of an existing word after verifying ownership.
    Returns a dictionary with a success message and the word_id.
    Raises NotFoundError, ForbiddenError, or WordServiceError.
    """
    try:
        # First we check existence and verify ownership
        old_word_data = _get_and_verify_word_ownership(
            db, user_id, word_id, fetch_subcollections=True
        )

        # # Check if the new text is actually different from the old one (optional, but good UX)
        # # This prevents an unnecessary DB write if the text is the same.
        # if old_word_data.get("word_text") == new_word_text:
        #     return {
        #         "message": f"Word text for ID '{word_id}' is already '{new_word_text}'. No update performed.",
        #         "word_id": word_id,
        #         "updated_word_details": old_word_data # Return the existing data
        #     }

        wd.edit_word_by_id(db, word_id, new_word_text)

        # To return the *updated* word, we should fetch it again AFTER the update.
        # The 'old_word_data' is from before the update.
        # The DAL's edit_word_by_id doesn't return the updated document.
        # So, let's call the helper again to get the fresh data.

        new_word_data = _get_and_verify_word_ownership(
            db, user_id, word_id, fetch_subcollections=True
        )
        # Note: old_word_data['word_text'] would still have the old text.
        # new_word_data_with_id['word_text'] will have the new_word_text.
        print(
            f"WordService: Word ID '{word_id}' text updated from '{old_word_data.get('word_text')}' to '{new_word_data.get('word_text')}' for user '{user_id}'."
        )
        return {
            "message": f"Word '{old_word_data.get('word_text', word_id)}' successfully updated to '{new_word_data.get('word_text')}'.",
            "word_id": word_id,
            "updated_word_details": new_word_data,
        }
    except NotFoundError:
        raise
    except DatabaseError as de:
        print(
            f"WordService: DatabaseError updating text for word '{word_id}', user '{user_id}': {str(de)}"
        )
        raise WordServiceError(
            "Could not update word text due to a data access issue."
        ) from de
    except Exception as e:
        print(
            f"WordService: Unexpected error updating text for word '{word_id}', user '{user_id}': {str(e)}"
        )
        raise WordServiceError(
            "An unexpected service error occurred while updating word text."
        ) from e


def delete_word_for_user(db, user_id: str, word_id: str) -> dict:
    """
    Deletes a word for a user after verifying existence and ownership.
    Returns a success message dictionary.
    Raises NotFoundError if word not found/owned, or WordServiceError for other issues.
    """
    try:
        word_to_delete_data = _get_and_verify_word_ownership(
            db, user_id, word_id, fetch_subcollections=False
        )

        wd.delete_word_by_id(db, word_id)
        print(
            f"WordService: Word ID '{word_id}' (text: '{word_to_delete_data['word_text']}') deleted for user '{user_id}'."
        )

        return {
            "message": f"Word '{word_to_delete_data['word_text']}' deleted successfully.",
            "word_id": word_id,
        }
    except NotFoundError:
        raise
    except DatabaseError as de:
        print(
            f"WordService: DatabaseError deleting word '{word_id}' for user '{user_id}': {str(de)}"
        )
        raise WordServiceError(
            "Could not delete word due to a data access issue."
        ) from de
    except Exception as e:
        print(
            f"WordService: Unexpected error deleting word '{word_id}' for user '{user_id}': {str(e)}"
        )
        raise WordServiceError(
            "An unexpected service error occurred while deleting word."
        ) from e


def list_words_for_user(db, user_id):
    try:
        word_snapshots = wd.get_all_words_for_user_sorted_by_stars(db, user_id)
        results_list = []
        for snapshot in word_snapshots:
            word_data = snapshot.to_dict()
            word_id = snapshot.id
            word_data["word_id"] = word_id
            word_data["descriptions"] = wd.get_all_descriptions_for_word(db, word_id)
            word_data["examples"] = wd.get_all_examples_for_word(db, word_id)

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
    db,
    user_id: str,
    word_id: str,
    description_text: str,
    initial_description: bool = False,
):
    """
    Adds a description to an existing word, after verifying ownership.
    Returns details including the new description's ID.
    """
    try:
        # We don't need the word data here, because we are going to add a description, not getting word details.
        # The function will automatically raise an error if the word doesn't exist or the user doesn't own it.
        _ = _get_and_verify_word_ownership(db, user_id, word_id)
        # If this check passes then we can add the description.
        description_data = {
            "description_text": description_text,
            "word_id": word_id,
            "is_initial": initial_description,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
            "user_id": user_id,
        }
        new_description_ref = wd.append_description_to_word_db(
            db, word_id, description_data
        )
        new_description_id = new_description_ref.id

        return {
            "message": f"Description added successfully to word '{word_id}'.",
            "word_id": word_id,
            "description_id": new_description_id,
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


def add_example_for_user(
    db,
    user_id: str,
    word_id: str,
    example_text: str,
    initial_example: bool = False,
):
    """
    Adds a example to an existing word, after verifying ownership.
    Returns details including the new description's ID.
    """
    try:
        # We don't need the word data here, because we are going to add a example, not getting word details.
        # The function will automatically raise an error if the word doesn't exist or the user doesn't own it.
        _ = _get_and_verify_word_ownership(db, user_id, word_id)
        # If this check passes then we can add the example.
        example_data = {
            "example_text": example_text,
            "word_id": word_id,
            "is_initial": initial_example,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
            "user_id": user_id,
        }
        new_example_ref = wd.append_example_to_word_db(db, word_id, example_data)
        new_example_id = new_example_ref.id

        return {
            "message": f"Example added successfully to word '{word_id}'.",
            "word_id": word_id,
            "example_id": new_example_id,
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


def get_word_details_for_user(db, user_id: str, word_id: str) -> dict:
    """
    Fetches details for a specific word if it exists and belongs to the user.
    """
    word_data_with_id = _get_and_verify_word_ownership(
        db, user_id, word_id, fetch_subcollections=True
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
            f"STAR_WORD: Star updated for word ID '{word_id}' (text: '{word_text}') for user_id: {user_id}. New stars: {new_star_count}"
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
