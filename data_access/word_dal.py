import logging

from firebase_admin import firestore

from utils import DatabaseError, timed_execution

logger = logging.getLogger("infinite_vocab_app")


@timed_execution(logger, "Word Query")
def _execute_word_query(
    db,
    user_id: str,
    additional_filters: list = None,  # List of tuples: [("field", "op", "value")]
    order_by_config: tuple = None,  # Tuple: ("field", "direction_constant_or_string")
    limit_count: int = None,
):
    try:
        # Log query parameters at DEBUG level
        filter_desc = ", ".join(
            [f"{f}:{op}:{v}" for f, op, v in (additional_filters or [])]
        )
        order_desc = (
            f"{order_by_config[0]}:{order_by_config[1]}" if order_by_config else "none"
        )
        logger.debug(
            f"DAL: Executing query on collection='words' with filters=[user_id={user_id}, {filter_desc}], "
            f"ordering={order_desc}, limit={limit_count}"
        )

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
        # Log query results at DEBUG level
        logger.debug(
            f"DAL: Query complete on collection='words' - found {len(snapshots)} documents for user {user_id}"
        )
        return snapshots
    except Exception as e:
        logger.error(
            f"DAL: Error in _execute_word_query for user {user_id}: {str(e)}",
            exc_info=True,
        )
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
    logger.info(f"DAL: Finding word by text '{word_text}' for user {user_id}")
    filters = [("word_text", "==", word_text)]
    return _execute_word_query(db, user_id, additional_filters=filters, limit_count=1)


def get_word_by_id(db, word_id):
    """Fetches a single word document from Firestore by its ID."""
    # We skip ownership checks here since this isn't a transaction.
    # It's more of a service layer's job.
    try:
        logger.info(f"DAL: Attempting to fetch word by ID: '{word_id}'")
        doc_ref = db.collection("words").document(word_id)
        snapshot = doc_ref.get()
        return snapshot
    except Exception as e:
        logger.error(
            f"DAL: Error fetching word by ID '{word_id}': {str(e)}", exc_info=True
        )
        raise DatabaseError(
            f"DAL: Firestore error fetching word by ID '{word_id}': {str(e)}"
        ) from e


def update_word_by_id(db, word_id, new_word_text):
    """
    Updates the 'word_text' and 'updatedAt' timestamp for a specific word document.
    Returns True on success. Raises DatabaseError on failure.
    """
    try:
        word_ref = db.collection("words").document(word_id)
        data_to_update = {
            "word_text": new_word_text,
            "updatedAt": firestore.SERVER_TIMESTAMP,
        }
        word_ref.update(data_to_update)
        logger.info(f"DAL: Updated word text for ID '{word_id}' to '{new_word_text}'")
        return True
    except Exception as e:
        logger.error(
            f"DAL: Error updating word text for ID '{word_id}' to '{new_word_text}': {str(e)}",
            exc_info=True,
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

        logger.info(f"DAL: Successfully deleted word with ID '{word_id}'")
        return True
    except Exception as e:
        logger.error(
            f"DAL: Error deleting word ID '{word_id}': {str(e)}", exc_info=True
        )
        raise DatabaseError(
            f"DAL: Firestore error deleting word ID '{word_id}': {str(e)}"
        ) from e


def get_all_words_for_user_sorted_by_stars(db, user_id: str):
    """Gets all words for a user, sorted by word_stars descending."""
    logger.info(f"DAL: Getting all words for user {user_id}, sorted by word_stars")
    order_config = ("word_stars", "DESCENDING")
    return _execute_word_query(db, user_id, order_by_config=order_config)


def add_word_to_db(db, data_to_save: dict):
    try:
        timestamp, doc_ref = db.collection("words").add(data_to_save)
        logger.info(f"DAL: Word added to Firestore with ID: {doc_ref.id}")
        return timestamp, doc_ref
    except Exception as e:
        logger.error(
            f"DAL: Failed to add word data to Firestore: {str(e)}", exc_info=True
        )
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
        logger.info(
            f"DAL: New description added with ID {new_description_ref.id} to word '{word_id}'"
        )
        return new_description_ref
    except Exception as e:
        logger.error(
            f"DAL: Failed to append description to word '{word_id}': {str(e)}",
            exc_info=True,
        )
        raise DatabaseError(
            f"DAL: Could not add description for word '{word_id}' due to Firestore error."
        ) from e


def update_description_to_word_db(
    db, word_id: str, description_id: str, description_text: str
):
    """Updates the description text and updatedAt timestamp for a specific description document."""
    try:
        description_ref = (
            db.collection("words")
            .document(word_id)
            .collection("descriptions")
            .document(description_id)
        )
        data_to_update = {
            "description_text": description_text,
            "updatedAt": firestore.SERVER_TIMESTAMP,
        }
        description_ref.update(data_to_update)
        logger.info(
            f"DAL: Updated description text for ID '{description_id}' in word '{word_id}' to '{description_text}'"
        )
        return True
    except Exception as e:
        logger.error(
            f"DAL: Error updating description text for ID '{description_id}' in word '{word_id}': {str(e)}",
            exc_info=True,
        )
        raise DatabaseError(
            f"DAL: Firestore error updating description text for ID '{description_id}' in word '{word_id}': {str(e)}"
        ) from e


def delete_description_from_word_db(db, word_id: str, description_id: str):
    """
    Deletes a description document from a word's descriptions subcollection.
    Returns True on success. Raises DatabaseError on failure.
    """
    try:
        description_ref = (
            db.collection("words")
            .document(word_id)
            .collection("descriptions")
            .document(description_id)
        )
        description_ref.delete()
        logger.info(
            f"DAL: Successfully deleted description with ID '{description_id}' from word '{word_id}'"
        )
        return True
    except Exception as e:
        logger.error(
            f"DAL: Error deleting description ID '{description_id}' from word '{word_id}': {str(e)}",
            exc_info=True,
        )
        raise DatabaseError(
            f"DAL: Firestore error deleting description ID '{description_id}' from word '{word_id}': {str(e)}"
        ) from e


def get_description_by_id(db, word_id: str, description_id: str):
    """Fetches a single description document from a word's descriptions subcollection by its ID."""
    try:
        logger.info(
            f"DAL: Attempting to fetch description by ID: '{description_id}' from word '{word_id}'"
        )
        description_ref = (
            db.collection("words")
            .document(word_id)
            .collection("descriptions")
            .document(description_id)
        )
        snapshot = description_ref.get()
        return snapshot
    except Exception as e:
        logger.error(
            f"DAL: Error fetching description by ID '{description_id}' from word '{word_id}': {str(e)}",
            exc_info=True,
        )
        raise DatabaseError(
            f"DAL: Firestore error fetching description by ID '{description_id}' from word '{word_id}': {str(e)}"
        ) from e


def update_example_to_word_db(db, word_id: str, example_id: str, example_text: str):
    """Updates the example text and updatedAt timestamp for a specific example document."""
    try:
        example_ref = (
            db.collection("words")
            .document(word_id)
            .collection("examples")
            .document(example_id)
        )
        data_to_update = {
            "example_text": example_text,
            "updatedAt": firestore.SERVER_TIMESTAMP,
        }
        example_ref.update(data_to_update)
        logger.info(
            f"DAL: Updated example text for ID '{example_id}' in word '{word_id}' to '{example_text}'"
        )
        return True
    except Exception as e:
        logger.error(
            f"DAL: Error updating example text for ID '{example_id}' in word '{word_id}': {str(e)}",
            exc_info=True,
        )
        raise DatabaseError(
            f"DAL: Firestore error updating example text for ID '{example_id}' in word '{word_id}': {str(e)}"
        ) from e


def delete_example_from_word_db(db, word_id: str, example_id: str):
    """
    Deletes an example document from a word's examples subcollection.
    Returns True on success. Raises DatabaseError on failure.
    """
    try:
        example_ref = (
            db.collection("words")
            .document(word_id)
            .collection("examples")
            .document(example_id)
        )
        example_ref.delete()
        logger.info(
            f"DAL: Successfully deleted example with ID '{example_id}' from word '{word_id}'"
        )
        return True
    except Exception as e:
        logger.error(
            f"DAL: Error deleting example ID '{example_id}' from word '{word_id}': {str(e)}",
            exc_info=True,
        )
        raise DatabaseError(
            f"DAL: Firestore error deleting example ID '{example_id}' from word '{word_id}': {str(e)}"
        ) from e


def get_example_by_id(db, word_id: str, example_id: str):
    """Fetches a single example document from a word's examples subcollection by its ID."""
    try:
        logger.info(
            f"DAL: Attempting to fetch example by ID: '{example_id}' from word '{word_id}'"
        )
        example_ref = (
            db.collection("words")
            .document(word_id)
            .collection("examples")
            .document(example_id)
        )
        snapshot = example_ref.get()
        return snapshot
    except Exception as e:
        logger.error(
            f"DAL: Error fetching example by ID '{example_id}' from word '{word_id}': {str(e)}",
            exc_info=True,
        )
        raise DatabaseError(
            f"DAL: Firestore error fetching example by ID '{example_id}' from word '{word_id}': {str(e)}"
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
        logger.info(
            f"DAL: New example added with ID {new_example_ref.id} to word '{word_id}'"
        )
        return new_example_ref
    except Exception as e:
        logger.error(
            f"DAL: Failed to append example to word '{word_id}': {str(e)}",
            exc_info=True,
        )
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
        logger.info(
            f"DAL: Retrieved {len(descriptions_list)} descriptions for word '{word_id}'"
        )
        return descriptions_list
    except Exception as e:
        logger.error(
            f"DAL: Failed to get descriptions for word '{word_id}': {str(e)}",
            exc_info=True,
        )
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
        logger.info(
            f"DAL: Retrieved {len(examples_list)} examples for word '{word_id}'"
        )
        return examples_list
    except Exception as e:
        logger.error(
            f"DAL: Failed to get examples for word '{word_id}': {str(e)}", exc_info=True
        )
        raise DatabaseError(
            f"DAL: Could not retrieve examples for word '{word_id}' due to Firestore error: {str(e)}"
        ) from e


@firestore.transactional
@timed_execution(logger, "Word Star Transaction")
def atomic_update(transaction, db, word_id, user_id):
    try:
        logger.debug(
            f"DAL: Starting transaction for starring word '{word_id}' by user '{user_id}'"
        )
        # Read
        word_doc_ref = db.collection("words").document(word_id)
        snapshot = word_doc_ref.get(transaction=transaction)

        # We add checks here since this *is* part of a transaction.
        if not snapshot.exists:
            return "NOT_FOUND"

        word_data = snapshot.to_dict()

        if word_data.get("user_id") != user_id:
            return "FORBIDDEN"

        word_text = word_data.get("word_text")

        # Modify
        current_stars = word_data.get("word_stars", 0)
        new_star_count = current_stars + 1

        # Write
        transaction.update(
            word_doc_ref,
            {"word_stars": new_star_count, "updatedAt": firestore.SERVER_TIMESTAMP},
        )
        return (new_star_count, word_text)
    except Exception as e:
        logger.error(
            f"DAL: Error starring words for user {user_id}, word '{word_text}': {str(e)}",
            exc_info=True,
        )
        raise DatabaseError(
            f"DAL: Firestore error while querying words: {str(e)}"
        ) from e
