from firebase_admin import firestore

from utils.exceptions import DatabaseError


def _execute_word_query(
    db,
    user_uid: str,
    additional_filters: list = None,  # List of tuples: [("field", "op", "value")]
    order_by_config: tuple = None,  # Tuple: ("field", "direction_constant_or_string")
    limit_count: int = None,
):
    try:
        query = db.collection("words").where(
            filter=firestore.FieldFilter("user_uid", "==", user_uid)
        )
        if additional_filters:
            # Apply any extra filter conditions passed in the 'additional_filters' list.
            # Currently it is only one filter,
            # which is the word == word_text filter
            for field, op, value in additional_filters:
                query = query.where(
                    filter=firestore.FieldFilter(field, op, value)
                )
        if order_by_config:
            sort_field, sort_direction = order_by_config
            query = query.order_by(
                field_path=sort_field, direction=sort_direction
            )
        if (
            limit_count is not None
            and isinstance(limit_count, int)
            and limit_count > 0
        ):
            query = query.limit(limit_count)

        snapshots = list(query.stream())
        # Optional: More generic print or remove if too noisy for a helper
        # print(f"DAL (_execute_word_query for user {user_uid}): Found {len(snapshots)} docs.")
        return snapshots
    except Exception as e:
        print(
            f"DAL_ERROR: Error in _execute_word_query for user {user_uid}: {str(e)}"
        )
        raise DatabaseError(
            f"DAL: Firestore error during word query execution: {str(e)}"
        ) from e


def find_word_by_text_for_user(db, user_uid: str, word_text: str):
    """Finds a specific word by its text for a given user, expects 0 or 1 result."""
    print(f"DAL: Finding word by text '{word_text}' for user {user_uid}")
    filters = [("word", "==", word_text)]
    return _execute_word_query(
        db, user_uid, additional_filters=filters, limit_count=1
    )


def get_all_words_for_user_sorted_by_stars(db, user_uid: str):
    """Gets all words for a user, sorted by stars descending."""
    print(f"DAL: Getting all words for user {user_uid}, sorted by stars")
    order_config = ("stars", "DESCENDING")
    return _execute_word_query(db, user_uid, order_by_config=order_config)


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
