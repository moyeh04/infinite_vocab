from firebase_admin import firestore

from utils.exceptions import DatabaseError


def _execute_word_query(
    db,
    user_id: str,
    additional_filters: list = None,  # List of tuples: [("field", "op", "value")]
    order_by_config: tuple = None,  # Tuple: ("field", "direction_constant_or_string")
    limit_count: int = None,
):
    try:
        query = db.collection("words").where(
            filter=firestore.FieldFilter("user_id", "==", user_id)
        )
        if additional_filters:
            # Apply any extra filter conditions passed in the 'additional_filters' list.
            # Currently it is only one filter,
            # which is the word == word_text filter
            for field, op, value in additional_filters:
                query = query.where(filter=firestore.FieldFilter(field, op, value))
        if order_by_config:
            sort_field, sort_direction = order_by_config
            query = query.order_by(field_path=sort_field, direction=sort_direction)
        if limit_count is not None and isinstance(limit_count, int) and limit_count > 0:
            query = query.limit(limit_count)

        snapshots = list(query.stream())
        # Optional: More generic print or remove if too noisy for a helper
        # print(f"DAL (_execute_word_query for user {user_id}): Found {len(snapshots)} docs.")
        return snapshots
    except Exception as e:
        print(f"DAL_ERROR: Error in _execute_word_query for user {user_id}: {str(e)}")
        raise DatabaseError(
            f"DAL: Firestore error during word query execution: {str(e)}"
        ) from e


def find_word_by_text_for_user(db, user_id: str, word_text: str):
    """
    Finds a specific word by its text for a given user, expects 0 or 1 result.

    Important:
        This DAL function is tailored for checking if a word entry with the exact
        text already exists for the specified user, primarily for duplicate prevention.
        It calls the generic _execute_word_query with a limit of 1.
    """
    print(f"DAL: Finding word by text '{word_text}' for user {user_id}")
    filters = [("word", "==", word_text)]
    return _execute_word_query(db, user_id, additional_filters=filters, limit_count=1)


def get_word_by_id(db, word_id):
    """Fetches a single word document from Firestore by its ID."""
    # We skip ownership checks here since this isn't a transaction.
    # It's more of a service layer's job.
    try:
        print(f"DAL: Attempting to fetch word by ID: '{word_id}'")
        doc_ref = db.collection("words").document(word_id)
        snapshot = doc_ref.get()
        return snapshot
    except Exception as e:
        print(f"DAL_ERROR: Error fetching word by ID '{word_id}': {str(e)}")
        raise DatabaseError(
            f"DAL: Firestore error fetching word by ID '{word_id}': {str(e)}"
        ) from e


def edit_word_by_id(db, word_id, new_word_text):
    """
    Updates the 'word' text and 'updatedAt' timestamp for a specific word document.
    Returns True on success. Raises DatabaseError on failure.
    """
    try:
        word_ref = db.collection("words").document(word_id)
        data_to_update = {
            "word": new_word_text,
            "updatedAt": firestore.SERVER_TIMESTAMP,
        }
        word_ref.update(data_to_update)
        print(f"DAL: Updated word text for ID '{word_id}' to '{new_word_text}'")
        return True
    except Exception as e:
        print(
            f"DAL_ERROR: Error updating word text for ID '{word_id}' to '{new_word_text}': {str(e)}"
        )
        raise DatabaseError(
            f"DAL: Firestore error updating word text for ID '{word_id}' to '{new_word_text}': {str(e)}"
        ) from e


def delete_word_by_id(db, word_id: str):
    """
    Deletes a word document from Firestore by its ID.
    Returns True on success. Raises DatabaseError on failure.
    """
    try:
        example_snapshots = (
            db.collection("words").document(word_id).collection("examples").stream()
        )
        [doc_snapshot.reference.delete() for doc_snapshot in example_snapshots]

        desc_snapshots = (
            db.collection("words").document(word_id).collection("descriptions").stream()
        )
        [doc_snapshot.reference.delete() for doc_snapshot in desc_snapshots]

        _ = db.collection("words").document(word_id).delete()

        print(f"DAL: Successfully deleted word with ID '{word_id}'")
        return True
    except Exception as e:
        print(f"DAL_ERROR: Error deleting word ID '{word_id}': {str(e)}")
        raise DatabaseError(
            f"DAL: Firestore error deleting word ID '{word_id}': {str(e)}"
        ) from e


def get_all_words_for_user_sorted_by_stars(db, user_id: str):
    """Gets all words for a user, sorted by stars descending."""
    print(f"DAL: Getting all words for user {user_id}, sorted by stars")
    order_config = ("stars", "DESCENDING")
    return _execute_word_query(db, user_id, order_by_config=order_config)


def add_word_to_db(db, data_to_save: dict):
    try:
        timestamp, doc_ref = db.collection("words").add(data_to_save)
        print(f"DAL: Word added to Firestore with ID: {doc_ref.id}")
        return timestamp, doc_ref
    except Exception as e:
        print(f"DAL_ERROR: Failed to add word data to Firestore: {str(e)}")
        raise DatabaseError(f"DAL: Firestore error while adding word: {str(e)}") from e


def append_description_to_word_db(db, word_id: str, description_data: dict):
    """Adds a new description document to the specified word's 'descriptions' subcollection."""
    try:
        _timestamp, new_description_ref = (
            db.collection("words")
            .document(word_id)
            .collection("descriptions")
            .add(description_data)
        )
        print(
            f"DAL: New description added with ID {new_description_ref.id} to word '{word_id}'"
        )
        return new_description_ref
    except Exception as e:
        print(f"DAL_ERROR: Failed to append description to word '{word_id}': {str(e)}")
        raise DatabaseError(
            f"DAL: Could not add description for word '{word_id}' due to Firestore error."
        ) from e


def append_example_to_word_db(db, word_id: str, example_data: dict):
    """Adds a new example document to the specified word's 'examples' subcollection."""
    try:
        _timestamp, new_example_ref = (
            db.collection("words")
            .document(word_id)
            .collection("examples")
            .add(example_data)
        )
        print(
            f"DAL: New example added with ID {new_example_ref.id} to word '{word_id}'"
        )
        return new_example_ref
    except Exception as e:
        print(f"DAL_ERROR: Failed to append example to word '{word_id}': {str(e)}")
        raise DatabaseError(
            f"DAL: Could not add example for word '{word_id}' due to Firestore error."
        ) from e


def get_all_descriptions_for_word(db, word_id: str) -> list:
    """
    Fetches all description documents for a given word_id from its 'descriptions' subcollection.
    """

    try:
        descriptions_list = []
        # Construct the reference to the subcollection
        descriptions_ref = (
            db.collection("words").document(word_id).collection("descriptions")
        )

        desc_snapshots = descriptions_ref.order_by("createdAt").stream()
        for desc_snap in desc_snapshots:
            if desc_snap.exists:
                description_data = desc_snap.to_dict()
                description_data["description_id"] = desc_snap.id
                descriptions_list.append(description_data)
        return descriptions_list
    except Exception as e:
        print(f"DAL_ERROR: Failed to get descriptions for word '{word_id}': {str(e)}")
        raise DatabaseError(
            f"DAL: Could not retrieve descriptions for word '{word_id}' due to Firestore error: {str(e)}"
        ) from e


def get_all_examples_for_word(db, word_id: str) -> list:
    """
    Fetches all example documents for a given word_id from its 'examples' subcollection.
    """
    try:
        examples_list = []
        # Construct the reference to the subcollection
        examples_ref = db.collection("words").document(word_id).collection("examples")

        example_snapshots = examples_ref.order_by("createdAt").stream()
        for example_snap in example_snapshots:
            if example_snap.exists:
                example_data = example_snap.to_dict()
                example_data["example_id"] = example_snap.id
                examples_list.append(example_data)
        return examples_list
    except Exception as e:
        print(f"DAL_ERROR: Failed to get examples for word '{word_id}': {str(e)}")
        raise DatabaseError(
            f"DAL: Could not retrieve examples for word '{word_id}' due to Firestore error: {str(e)}"
        ) from e


@firestore.transactional
def atomic_update(transaction, db, word_id, user_id):
    try:
        # Read
        word_doc_ref = db.collection("words").document(word_id)
        snapshot = word_doc_ref.get(transaction=transaction)

        # We add checks here since this *is* part of a transaction.
        if not snapshot.exists:
            return "NOT_FOUND"

        word_data = snapshot.to_dict()

        if word_data.get("user_id") != user_id:
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
            f"DAL_ERROR: Error starring words for user {user_id}, word '{word_text}': {str(e)}"
        )
        raise DatabaseError(
            f"DAL: Firestore error while querying words: {str(e)}"
        ) from e
