from firebase_admin import firestore

from data_access import word_dal as wd
from utils.exceptions import (
    DatabaseError,
    DuplicateEntryError,
    ForbiddenError,
    NotFoundError,
    WordServiceError,
)


def create_word_for_user(db, uid, word_text_to_add):
    try:
        existing_words = wd.find_words_by_user_and_text(
            db, uid, word_text_to_add
        )
        if existing_words:
            existing_doc_id = existing_words[0].id
            print("--------------------------------------------------")
            print(
                f"Duplicate found: Word '{word_text_to_add}' already exists for user '{uid}' (Existing Doc ID: {existing_doc_id})."
            )
            print("--------------------------------------------------")
            raise DuplicateEntryError(
                f"Word '{word_text_to_add}' already exists in your list.",
                conflicting_id=existing_doc_id,
            )

        data_to_save = {
            "word": word_text_to_add,
            "stars": 0,
            "user_uid": uid,
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
            "A problem occurred with data storage while creating your word."
        ) from de

    except Exception as e:
        print(
            f"WordService: Unexpected error in create_word_for_user: {str(e)}"
        )
        raise WordServiceError("An unexpected service error occurred.") from e


def star_word_for_user(db, uid, word_id):
    transaction = db.transaction()
    try:
        word_doc_ref = db.collection("words").document(word_id)

        atomic_result = wd.atomic_update(transaction, word_doc_ref, uid)

        if atomic_result == "NOT_FOUND":
            raise NotFoundError(f"Word with ID '{word_id}' not found.")
        elif atomic_result == "FORBIDDEN":
            raise ForbiddenError("You are not authorized to modify this word.")

        new_star_count, word_text = atomic_result

        print(
            f"STAR_WORD: Star updated for word ID '{word_id}' (text: '{word_text}') for UID: {uid}. New stars: {new_star_count}"
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
