from firebase_admin import firestore

from utils.exceptions import DatabaseError


def add_word_to_db(db, data_to_save: dict):
    try:
        timestamp, doc_ref = db.collection("words").add(data_to_save)
        print(f"DAL: Word added to Firestore with ID: {doc_ref.id}")
        return timestamp, doc_ref

    except Exception as e:
        print(f"DAL_ERROR: Failed to add word data to Firestore: {str(e)}")
        raise DatabaseError(
            f"DAL: Firestore error while adding word: {str(e)}"
        ) from e


def find_words_by_user_and_text(db, user_uid, word_text):
    try:
        query = (
            db.collection("words")
            .where(filter=firestore.FieldFilter("user_uid", "==", user_uid))
            .where(filter=firestore.FieldFilter("word", "==", word_text))
            .limit(1)
        )
        snapshots = list(query.stream())
        return snapshots
    except Exception as e:
        print(
            f"DAL_ERROR: Error querying words for user {user_uid}, word '{word_text}': {str(e)}"
        )
        raise DatabaseError(
            f"DAL: Firestore error while querying words: {str(e)}"
        ) from e
