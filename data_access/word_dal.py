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


def query_words(
    db,
    user_uid: str,
    word_text: str = None,
    order_by_field: str = None,
    order_by_direction: str = None,  # e.g., firestore.Query.DESCENDING or "DESCENDING"
    limit_count: int = None,
):
    try:
        query = db.collection("words").where(
            filter=firestore.FieldFilter("user_uid", "==", user_uid)
        )
        if word_text:  # Mainly for checking for Duplicate words
            query = query.where(
                filter=firestore.FieldFilter("word", "==", word_text)
            )
        if order_by_field:
            if order_by_direction:
                query = query.order_by(
                    field_path=order_by_field, direction=order_by_direction
                )
            else:
                query = query.order_by(
                    field_path=order_by_field
                )  # Defaults to ascending
        if (
            limit_count is not None
            and isinstance(limit_count, int)
            and limit_count > 0
        ):
            query = query.limit(limit_count)

        snapshots = list(query.stream())
        print(
            f"DAL: query_words for user {user_uid} found {len(snapshots)} docs. "
            f"(Filters: word_text='{word_text}', Order: '{order_by_field}' {order_by_direction}, Limit: {limit_count})"
        )
        return snapshots
    except Exception as e:
        print(f"DAL_ERROR: Error in query_words for user {user_uid}: {str(e)}")
        raise DatabaseError(
            f"DAL: Firestore error during general word query: {str(e)}"
        ) from e


@firestore.transactional
def atomic_update(transaction, db, word_id, current_user_uid):
    try:
        # Read
        word_doc_ref = db.collection("words").document(word_id)
        snapshot = word_doc_ref.get(transaction=transaction)

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
            word_doc_ref,
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
