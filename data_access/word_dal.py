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


@firestore.transactional
def atomic_update(transaction, doc_ref_to_update, current_user_uid):
    try:
        # Read
        snapshot = doc_ref_to_update.get(transaction=transaction)

        if not snapshot.exists:
            return "NOT_FOUND"

        word_data = snapshot.to_dict()

        if word_data.get("user_uid") != current_user_uid:
            return "FORBIDDEN"

        word_text = word_data.get("word")

        # Modify
        current_stars = word_data.get("stars", 0)
        new_star_count = current_stars + 1

        # Write
        transaction.update(
            doc_ref_to_update,
            {"stars": new_star_count, "updatedAt": firestore.SERVER_TIMESTAMP},
        )
        return (new_star_count, word_text)
    except Exception as e:
        print(
            f"DAL_ERROR: Error starring words for user {current_user_uid}, word '{word_text}': {str(e)}"
        )
        raise DatabaseError(
            f"DAL: Firestore error while querying words: {str(e)}"
        ) from e
