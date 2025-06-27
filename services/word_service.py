from firebase_admin import firestore

from data_access import word_dal as wd
from utils.exceptions import (
    DatabaseError,
    DuplicateEntryError,
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
