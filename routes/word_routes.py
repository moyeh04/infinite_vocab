import logging
from flask import Blueprint, g, request

from middleware import firebase_token_required
from services import word_service as ws
from utils import (
    # DatabaseError, # It will rise as WordServiceError
    DuplicateEntryError,
    ForbiddenError,
    NotFoundError,
    WordServiceError,
    camelized_response,
    decamelized_request,
    error_response,
)

logger = logging.getLogger("infinite_vocab_app")

words_bp = Blueprint("words_api", __name__, url_prefix="/api/v1/words")


@words_bp.before_request
def authenticate_before_request():
    # Log the incoming request
    logger.info(
        f"REQUEST: {request.method} {request.path} - User: {g.user_id if hasattr(g, 'user_id') else 'anonymous'}"
    )
    return firebase_token_required()


@words_bp.route("/check-existence", methods=["POST"])
def check_word_existence():
    request_data = request.get_json()
    if not request_data:
        return error_response("Missing or invalid JSON request body", 400)

    # Convert camelCase from frontend to snake_case for Python
    request_data = decamelized_request(request_data)

    word_text = request_data.get("word_text")
    if not word_text or not word_text.strip():
        return error_response("Missing or empty 'wordText' field in JSON body", 400)
    word_text = word_text.strip()

    logger.info(
        f"ROUTE: Checking existence for word '{word_text}' for user_id {g.user_id}"
    )
    try:
        existence_details = ws.check_word_exists(g.db, g.user_id, word_text)
        return camelized_response(existence_details, 200)
    except WordServiceError as e:
        logger.warning(
            f"ROUTE: WordServiceError during check_existence for word '{word_text}', user_id {g.user_id}: {str(e)}"
        )
        return error_response(e.message, e.status_code, e.context)
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error in check_existence for word '{word_text}', user_id {g.user_id}: {str(e)}",
            exc_info=True,
        )
        return error_response(
            "An unexpected error occurred while checking word existence.", 500
        )


@words_bp.route("/", methods=["POST"])
def create_word():
    request_data = request.get_json()
    if not request_data:
        return error_response("Missing or invalid JSON request body", 400)

    # Convert camelCase from frontend to snake_case for Python
    request_data = decamelized_request(request_data)

    word_text = request_data.get("word_text")
    if not word_text or not word_text.strip():
        return error_response("Missing or empty 'wordText' field in JSON body", 400)
    word_text = word_text.strip()

    initial_description = request_data.get("description_text")
    if not initial_description or not initial_description.strip():
        return error_response(
            "Missing or empty 'descriptionText' field in JSON body", 400
        )
    initial_description = initial_description.strip()

    initial_example = request_data.get("example_text")
    if not initial_example or not initial_example.strip():
        return error_response("Missing or empty 'exampleText' field in JSON body", 400)
    initial_example = initial_example.strip()

    logger.info(
        f"ROUTE: Input validation passed. Word to add: {word_text}, Description: {initial_description}, Example: {initial_example}"
    )

    try:
        new_word_details = ws.create_word_for_user(
            g.db, g.user_id, word_text, initial_description, initial_example
        )
        logger.info(
            f"ROUTE: Successfully created word '{word_text}' for user_id {g.user_id}"
        )
        return camelized_response(new_word_details, 201)
    except DuplicateEntryError as e:
        logger.warning(f"ROUTE: Duplicate word - {str(e)}")
        return camelized_response(
            {
                "message": e.message,  # Or str(e)
                "existing_word_id": e.conflicting_id,
            },
            e.status_code,  # Use status_code from exception (will be 409)
        )
    except WordServiceError as e:
        logger.error(f"ROUTE: WordServiceError - {str(e)}")
        return error_response(e.message, e.status_code, e.context)
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error in create_word for user_id {g.user_id}: {str(e)}",
            exc_info=True,
        )
        return error_response("An unexpected server error occurred", 500)


@words_bp.route("/", methods=["GET"])
def list_words():
    logger.info(f"ROUTE: Attempting to fetch words for user_id: {g.user_id}")
    try:
        word_list_data = ws.list_words_for_user(g.db, g.user_id)
        logger.info(
            f"ROUTE: Successfully fetched {len(word_list_data)} words for user_id: {g.user_id}"
        )
        return camelized_response(word_list_data, 200)
    except WordServiceError as e:
        logger.error(
            f"ROUTE: WordServiceError fetching words for user_id {g.user_id}: {str(e)}"
        )
        return error_response(e.message, e.status_code, e.context)
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error fetching words for user_id {g.user_id}: {str(e)}",
            exc_info=True,
        )
        return error_response("An error occurred while fetching words", 500)


@words_bp.route("/<word_id>", methods=["GET"])
def get_word_details(word_id: str):
    logger.info(
        f"ROUTE: Attempting to fetch word details for word_id: {word_id}, user_id: {g.user_id}"
    )
    try:
        word_details = ws.get_word_details_for_user(g.db, g.user_id, word_id)
        logger.info(
            f"ROUTE: Successfully fetched word details for word_id: {word_id}, user_id: {g.user_id}"
        )
        return camelized_response(word_details, 200)
    except NotFoundError as e:
        logger.warning(
            f"ROUTE: NotFoundError for word_id {word_id}, user_id {g.user_id} - {str(e)}"
        )
        return error_response(str(e), e.status_code)
    except WordServiceError as e:
        logger.error(
            f"ROUTE: WordServiceError for word_id {word_id}, user_id {g.user_id} - {str(e)}"
        )
        return error_response(e.message, e.status_code, e.context)
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error in get_word_details_route for word_id {word_id}, user_id {g.user_id}: {str(e)}",
            exc_info=True,
        )
        return error_response("An unexpected server error occurred", 500)


@words_bp.route("/<word_id>", methods=["PATCH"])
def update_word(word_id: str):
    try:
        request_data = request.get_json()
        if not request_data:
            return error_response("Missing or invalid JSON request body", 400)

        # Convert camelCase from frontend to snake_case for Python
        request_data = decamelized_request(request_data)

        word_text = request_data.get("word_text")
        if not word_text or not word_text.strip():
            return error_response("Missing or empty 'wordText' field in JSON body", 400)
        word_text = word_text.strip()

        logger.info(f"ROUTE: Input validation passed. Word to rename: {word_text}")
        success_data = ws.update_word_for_user(g.db, g.user_id, word_id, word_text)
        logger.info(
            f"ROUTE: Successfully updated word_id {word_id} for user_id {g.user_id}"
        )
        return camelized_response(success_data, 200)
    except NotFoundError as e:
        logger.warning(f"ROUTE: Word not found - {str(e)}")
        return error_response(str(e), e.status_code)
    except ForbiddenError as e:
        logger.warning(f"ROUTE: Forbidden to update word - {str(e)}")
        return error_response(str(e), e.status_code)
    except WordServiceError as e:
        logger.error(f"ROUTE: WordServiceError - {str(e)}")
        return error_response(e.message, e.status_code, e.context)
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error in update_word_for_user for word_id {word_id}: {str(e)}",
            exc_info=True,
        )
        return error_response("An unexpected server error occurred", 500)


@words_bp.route("/<word_id>", methods=["DELETE"])
def delete_word(word_id: str):
    """
    Delete a word associated with the current user.
    """
    try:
        logger.info(f"ROUTE: Deleting word {word_id} for user {g.user_id}")
        success_data = ws.delete_word_for_user(g.db, g.user_id, word_id)
        logger.info(f"ROUTE: Successfully deleted word {word_id} for user {g.user_id}")
        return camelized_response(success_data, 200)
    except NotFoundError as e:
        logger.warning(
            f"ROUTE: Word {word_id} not found for user {g.user_id}: {str(e)}"
        )
        return error_response(str(e), e.status_code)
    except WordServiceError as e:
        logger.error(
            f"ROUTE: Service error deleting word {word_id} for user {g.user_id}: {e.message}"
        )
        return error_response(e.message, e.status_code, e.context)
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error deleting word {word_id} for user {g.user_id}: {str(e)}",
            exc_info=True,
        )
        return error_response("An unexpected server error occurred", 500)


@words_bp.route("/<word_id>/star", methods=["POST"])
def star_word(word_id):
    logger.info(f"ROUTE: Starring word {word_id} for user {g.user_id}")
    try:
        success_data = ws.star_word_for_user(g.db, g.user_id, word_id)
        logger.info(f"ROUTE: Successfully starred word {word_id} for user {g.user_id}")
        return camelized_response(success_data, 200)
    except NotFoundError as e:
        logger.warning(f"ROUTE: Word not found - {str(e)}")
        return error_response(str(e), e.status_code)
    except ForbiddenError as e:
        logger.warning(f"ROUTE: Forbidden to star word - {str(e)}")
        return error_response(str(e), e.status_code)
    except WordServiceError as e:
        logger.error(f"ROUTE: WordServiceError - {str(e)}")
        return error_response(e.message, e.status_code, e.context)
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error in star_word for word_id {word_id}: {str(e)}",
            exc_info=True,
        )
        return error_response("An unexpected server error occurred", 500)


@words_bp.route("/<word_id>/descriptions", methods=["POST"])
def add_description_to_word(word_id: str):
    logger.info(f"ROUTE: Adding description to word {word_id} for user {g.user_id}")
    try:
        request_data = request.get_json()
        if not request_data:
            return error_response("Missing or invalid JSON request body", 400)

        # Convert camelCase from frontend to snake_case for Python
        request_data = decamelized_request(request_data)

        description_text = request_data.get("description_text")
        if not description_text or not description_text.strip():
            return error_response(
                "Missing or empty 'descriptionText' field in JSON body", 400
            )
        description_text = description_text.strip()
        success_data = ws.add_description_for_user(
            g.db, g.user_id, word_id, description_text
        )
        logger.info(
            f"ROUTE: Successfully added description to word {word_id} for user {g.user_id}"
        )
        return camelized_response(success_data, 200)
    except NotFoundError as e:
        logger.warning(f"ROUTE: Word not found - {str(e)}")
        return error_response(str(e), e.status_code)
    except ForbiddenError as e:
        logger.warning(f"ROUTE: Forbidden to add a description to word - {str(e)}")
        return error_response(str(e), e.status_code)
    except WordServiceError as e:
        logger.error(f"ROUTE: WordServiceError - {str(e)}")
        return error_response(e.message, e.status_code, e.context)
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error in add_description_for_user for word_id {word_id}: {str(e)}",
            exc_info=True,
        )
        return error_response("An unexpected server error occurred", 500)


@words_bp.route("/<word_id>/descriptions/<description_id>", methods=["PATCH"])
def update_description_in_word(word_id: str, description_id: str):
    logger.info(
        f"ROUTE: Updating description {description_id} in word {word_id} for user {g.user_id}"
    )
    try:
        request_data = request.get_json()
        if not request_data:
            return error_response("Missing or invalid JSON request body", 400)

        # Convert camelCase from frontend to snake_case for Python
        request_data = decamelized_request(request_data)

        description_text = request_data.get("description_text")
        if not description_text or not description_text.strip():
            return error_response(
                "Missing or empty 'descriptionText' field in JSON body", 400
            )
        description_text = description_text.strip()

        success_data = ws.update_description_for_user(
            g.db, g.user_id, word_id, description_id, description_text
        )
        logger.info(
            f"ROUTE: Successfully updated description {description_id} in word {word_id} for user {g.user_id}"
        )
        return camelized_response(success_data, 200)
    except NotFoundError as e:
        logger.warning(f"ROUTE: Description not found - {str(e)}")
        return error_response(str(e), e.status_code)
    except ForbiddenError as e:
        logger.warning(f"ROUTE: Forbidden to update description - {str(e)}")
        return error_response(str(e), e.status_code)
    except WordServiceError as e:
        logger.error(f"ROUTE: WordServiceError - {str(e)}")
        return error_response(e.message, e.status_code, e.context)
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error in update_description_for_user for word_id {word_id}, description_id {description_id}: {str(e)}",
            exc_info=True,
        )
        return error_response("An unexpected server error occurred", 500)


@words_bp.route("/<word_id>/descriptions/<description_id>", methods=["DELETE"])
def delete_description_from_word(word_id: str, description_id: str):
    logger.info(
        f"ROUTE: Deleting description {description_id} from word {word_id} for user {g.user_id}"
    )
    try:
        success_data = ws.delete_description_for_user(
            g.db, g.user_id, word_id, description_id
        )
        logger.info(
            f"ROUTE: Successfully deleted description {description_id} from word {word_id} for user {g.user_id}"
        )
        return camelized_response(success_data, 200)
    except NotFoundError as e:
        logger.warning(
            f"ROUTE: Description {description_id} not found in word {word_id} for user {g.user_id}: {str(e)}"
        )
        return error_response(str(e), e.status_code)
    except WordServiceError as e:
        logger.error(
            f"ROUTE: Service error deleting description {description_id} from word {word_id} for user {g.user_id}: {e.message}"
        )
        return error_response(e.message, e.status_code, e.context)
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error deleting description {description_id} from word {word_id} for user {g.user_id}: {str(e)}",
            exc_info=True,
        )
        return error_response("An unexpected server error occurred", 500)


@words_bp.route("/<word_id>/examples/<example_id>", methods=["PATCH"])
def update_example_in_word(word_id: str, example_id: str):
    logger.info(
        f"ROUTE: Updating example {example_id} in word {word_id} for user {g.user_id}"
    )
    try:
        request_data = request.get_json()
        if not request_data:
            return error_response("Missing or invalid JSON request body", 400)

        # Convert camelCase from frontend to snake_case for Python
        request_data = decamelized_request(request_data)

        example_text = request_data.get("example_text")
        if not example_text or not example_text.strip():
            return error_response(
                "Missing or empty 'exampleText' field in JSON body", 400
            )
        example_text = example_text.strip()

        success_data = ws.update_example_for_user(
            g.db, g.user_id, word_id, example_id, example_text
        )
        logger.info(
            f"ROUTE: Successfully updated example {example_id} in word {word_id} for user {g.user_id}"
        )
        return camelized_response(success_data, 200)
    except NotFoundError as e:
        logger.warning(f"ROUTE: Example not found - {str(e)}")
        return error_response(str(e), e.status_code)
    except ForbiddenError as e:
        logger.warning(f"ROUTE: Forbidden to update example - {str(e)}")
        return error_response(str(e), e.status_code)
    except WordServiceError as e:
        logger.error(f"ROUTE: WordServiceError - {str(e)}")
        return error_response(e.message, e.status_code, e.context)
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error in update_example_for_user for word_id {word_id}, example_id {example_id}: {str(e)}",
            exc_info=True,
        )
        return error_response("An unexpected server error occurred", 500)


@words_bp.route("/<word_id>/examples/<example_id>", methods=["DELETE"])
def delete_example_from_word(word_id: str, example_id: str):
    logger.info(
        f"ROUTE: Deleting example {example_id} from word {word_id} for user {g.user_id}"
    )
    try:
        success_data = ws.delete_example_for_user(g.db, g.user_id, word_id, example_id)
        logger.info(
            f"ROUTE: Successfully deleted example {example_id} from word {word_id} for user {g.user_id}"
        )
        return camelized_response(success_data, 200)
    except NotFoundError as e:
        logger.warning(
            f"ROUTE: Example {example_id} not found in word {word_id} for user {g.user_id}: {str(e)}"
        )
        return error_response(str(e), e.status_code)
    except WordServiceError as e:
        logger.error(
            f"ROUTE: Service error deleting example {example_id} from word {word_id} for user {g.user_id}: {e.message}"
        )
        return error_response(e.message, e.status_code, e.context)
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error deleting example {example_id} from word {word_id} for user {g.user_id}: {str(e)}",
            exc_info=True,
        )
        return error_response("An unexpected server error occurred", 500)


@words_bp.route("/<word_id>/examples", methods=["POST"])
def add_example_to_word(word_id: str):
    logger.info(f"ROUTE: Adding example to word {word_id} for user {g.user_id}")
    try:
        request_data = request.get_json()
        if not request_data:
            return error_response("Missing or invalid JSON request body", 400)

        # Convert camelCase from frontend to snake_case for Python
        request_data = decamelized_request(request_data)

        example_text = request_data.get("example_text")
        if not example_text or not example_text.strip():
            return error_response(
                "Missing or empty 'exampleText' field in JSON body", 400
            )
        example_text = example_text.strip()
        success_data = ws.add_example_for_user(g.db, g.user_id, word_id, example_text)
        logger.info(
            f"ROUTE: Successfully added example to word {word_id} for user {g.user_id}"
        )
        return camelized_response(success_data, 200)
    except NotFoundError as e:
        logger.warning(f"ROUTE: Word not found - {str(e)}")
        return error_response(str(e), e.status_code)
    except ForbiddenError as e:
        logger.warning(f"ROUTE: Forbidden to add a example to word - {str(e)}")
        return error_response(str(e), e.status_code)
    except WordServiceError as e:
        logger.error(f"ROUTE: WordServiceError - {str(e)}")
        return error_response(e.message, e.status_code, e.context)
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error in add_example_for_user for word_id {word_id}: {str(e)}",
            exc_info=True,
        )
        return error_response("An unexpected server error occurred", 500)
