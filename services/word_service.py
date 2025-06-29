from firebase_admin import firestore

from data_access import word_dal as wd
from utils.exceptions import (
    DatabaseError,
    DuplicateEntryError,
    ForbiddenError,
    NotFoundError,
    WordServiceError,
)


def create_word_for_user(db, user_id, word_text_to_add):
    try:
        existing_words = wd.find_word_by_text_for_user(
            db, user_id, word_text_to_add
        )
        if existing_words:
            existing_doc_id = existing_words[0].id
            print("--------------------------------------------------")
            print(
                f"Duplicate found: Word '{word_text_to_add}' already exists for user '{user_id}' (Existing Doc ID: {existing_doc_id})."
            )
            print("--------------------------------------------------")
            raise DuplicateEntryError(
                f"Word '{word_text_to_add}' already exists in your list. Try adding a star to the existing entry instead?",
                conflicting_id=existing_doc_id,
            )

        data_to_save = {
            "word": word_text_to_add,
            "stars": 0,
            "user_id": user_id,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
        }

        _, new_word_ref = wd.add_word_to_db(db, data_to_save)

        print(f"Word added to Firestore with ID: {new_word_ref.id}")
        response_data = data_to_save.copy()
        response_data["word_id"] = new_word_ref.id
        # Remove createdAt/updatedAt fields because they hold SERVER_TIMESTAMP
        # sentinels which cannot be directly converted to JSON by jsonify.
        del response_data["createdAt"]
        del response_data["updatedAt"]

        return response_data
    except DuplicateEntryError:
        raise
    except DatabaseError as de:
        print(f"WordService: DatabaseError encountered: {str(de)}")
        raise WordServiceError(
            "A database problem occurred while creating your word."
        ) from de
    except Exception as e:
        print(
            f"WordService: Unexpected error in create_word_for_user: {str(e)}"
        )
        raise WordServiceError("An unexpected service error occurred.") from e


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


def get_word_details_for_user(db, current_user_uid: str, target_word_id: str):
    """
    Fetches details for a specific word if it exists and belongs to the user.
    Raises NotFoundError if word doesn't exist or doesn't belong to the user.
    Raises WordServiceError for other issues.
    """
    try:
        snapshot = wd.get_word_by_id(db, target_word_id)

        if not snapshot.exists:
            raise NotFoundError(f"Word with ID '{target_word_id}' not found.")

        word_data = snapshot.to_dict()

        # Ownership Check: Does the 'user_id' field in the word match the current user?
        if word_data.get("user_id") != current_user_uid:
            raise NotFoundError(
                f"Word with ID '{target_word_id}' not found or you do not have permission to view it."
            )

        word_data["word_id"] = snapshot.id
        return word_data
    except NotFoundError:
        raise
    except DatabaseError as de:
        print(
            f"WordService: DatabaseError fetching details for word ID '{target_word_id}': {str(de)}"
        )
        raise WordServiceError(
            "Could not retrieve word details due to a data access issue."
        ) from de
    except Exception as e:
        print(
            f"WordService: Unexpected error fetching details for word ID '{target_word_id}': {str(e)}"
        )
        raise WordServiceError(
            "An unexpected service error occurred while fetching word details."
        ) from e


def star_word_for_user(db, user_id, word_id):
    try:
        transaction = db.transaction()
        atomic_result = wd.atomic_update(transaction, db, word_id, user_id)

        if atomic_result == "NOT_FOUND":
            raise NotFoundError(f"Word with ID '{word_id}' not found.")
        elif atomic_result == "FORBIDDEN":
            raise ForbiddenError("You are not authorized to modify this word.")

        new_star_count, word_text = atomic_result

        print(
            f"STAR_WORD: Star updated for word ID '{word_id}' (text: '{word_text}') for UID: {user_id}. New stars: {new_star_count}"
        )
        return {
            "message": f"Successfully starred word '{word_text}'.",
            "word_id": word_id,
            "new_star_count": new_star_count,
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
