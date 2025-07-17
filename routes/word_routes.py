import logging
from flask import Blueprint, g, request, jsonify

from middleware import firebase_token_required
from services import word as ws
from schemas import (
    WordCreateSchema,
    WordUpdateSchema,
    WordExistenceCheckSchema,
    DescriptionCreateSchema,
    DescriptionUpdateSchema,
    ExampleCreateSchema,
    ExampleUpdateSchema,
)
from utils import (
    DuplicateEntryError,
    ForbiddenError,
    NotFoundError,
    WordServiceError,
    ValidationError,
)

logger = logging.getLogger("infinite_vocab_app")

words_bp = Blueprint("words_api", __name__, url_prefix="/api/v1/words")


@words_bp.before_request
def authenticate_before_request():
    # Log request BEFORE authentication
    logger.info(f"REQUEST: {request.method} {request.path}")
    return firebase_token_required()


@words_bp.route("/check-existence", methods=["POST"])
def check_word_existence():
    logger.info(f"ROUTE: check_word_existence invoked for user_id: {g.user_id}")
    try:
        data = request.get_json()
        schema = WordExistenceCheckSchema(**data)
        existence_details = ws.check_word_exists(g.db, g.user_id, schema.word_text)
        logger.info(
            f"ROUTE: Successfully checked existence for word '{schema.word_text}' for user_id {g.user_id}"
        )
        return jsonify(existence_details), 200
    except (ValidationError, ValueError) as e:
        logger.warning(
            f"ROUTE: Validation error for user {g.user_id} checking word existence: {e}"
        )
        return jsonify({"error": f"Invalid input: {e}"}), 400
    except WordServiceError as e:
        logger.warning(
            f"ROUTE: WordServiceError during check_existence for user_id {g.user_id}: {str(e)}"
        )
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error in check_existence for user_id {g.user_id}: {str(e)}",
            exc_info=True,
        )
        return jsonify(
            {"error": "An unexpected error occurred while checking word existence."}
        ), 500


@words_bp.route("/", methods=["POST"])
def create_word():
    logger.info(f"ROUTE: create_word invoked for user_id: {g.user_id}")
    try:
        data = request.get_json()
        schema = WordCreateSchema(**data)
        new_word = ws.create_word_for_user(g.db, g.user_id, schema)
        logger.info(
            f"ROUTE: Successfully created word '{schema.word_text}' for user_id {g.user_id}"
        )
        return jsonify(new_word.model_dump(by_alias=True)), 201
    except (ValidationError, ValueError) as e:
        logger.warning(
            f"ROUTE: Validation error for user {g.user_id} creating word: {e}"
        )
        return jsonify({"error": f"Invalid input: {e}"}), 400
    except DuplicateEntryError as e:
        logger.warning(f"ROUTE: Duplicate word - {str(e)}")
        return jsonify(
            {
                "error": e.message,
                "existingWordId": e.conflicting_id,
            }
        ), e.status_code
    except WordServiceError as e:
        logger.error(f"ROUTE: WordServiceError - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error in create_word for user_id {g.user_id}: {str(e)}",
            exc_info=True,
        )
        return jsonify({"error": "An unexpected server error occurred"}), 500


@words_bp.route("/", methods=["GET"])
def list_words():
    logger.info(f"ROUTE: list_words invoked for user_id: {g.user_id}")
    try:
        word_list = ws.list_words_for_user(g.db, g.user_id)
        logger.info(
            f"ROUTE: Successfully fetched {len(word_list)} words for user_id: {g.user_id}"
        )
        return jsonify([word.model_dump(by_alias=True) for word in word_list]), 200
    except WordServiceError as e:
        logger.error(
            f"ROUTE: WordServiceError fetching words for user_id {g.user_id}: {str(e)}"
        )
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error fetching words for user_id {g.user_id}: {str(e)}",
            exc_info=True,
        )
        return jsonify({"error": "An error occurred while fetching words"}), 500


@words_bp.route("/<word_id>", methods=["GET"])
def get_word_details(word_id: str):
    logger.info(
        f"ROUTE: get_word_details invoked for word_id: {word_id}, user_id: {g.user_id}"
    )
    try:
        word_details = ws.get_word_details_for_user(g.db, g.user_id, word_id)
        logger.info(
            f"ROUTE: Successfully fetched word details for word_id: {word_id}, user_id: {g.user_id}"
        )
        return jsonify(word_details.model_dump(by_alias=True)), 200
    except NotFoundError as e:
        logger.warning(
            f"ROUTE: NotFoundError for word_id {word_id}, user_id {g.user_id} - {str(e)}"
        )
        return jsonify({"error": str(e)}), e.status_code
    except WordServiceError as e:
        logger.error(
            f"ROUTE: WordServiceError for word_id {word_id}, user_id {g.user_id} - {str(e)}"
        )
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error in get_word_details for word_id {word_id}, user_id {g.user_id}: {str(e)}",
            exc_info=True,
        )
        return jsonify({"error": "An unexpected server error occurred"}), 500


@words_bp.route("/<word_id>", methods=["PATCH"])
def update_word(word_id: str):
    logger.info(
        f"ROUTE: update_word invoked for word_id: {word_id}, user_id: {g.user_id}"
    )
    try:
        data = request.get_json()
        schema = WordUpdateSchema(**data)
        updated_word = ws.update_word_for_user(g.db, g.user_id, word_id, schema)
        logger.info(
            f"ROUTE: Successfully updated word_id {word_id} for user_id {g.user_id}"
        )
        return jsonify(updated_word.model_dump(by_alias=True)), 200
    except (ValidationError, ValueError) as e:
        logger.warning(
            f"ROUTE: Validation error for user {g.user_id} updating word {word_id}: {e}"
        )
        return jsonify({"error": f"Invalid input: {e}"}), 400
    except NotFoundError as e:
        logger.warning(f"ROUTE: Word not found - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except ForbiddenError as e:
        logger.warning(f"ROUTE: Forbidden to update word - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except WordServiceError as e:
        logger.error(f"ROUTE: WordServiceError - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error in update_word for word_id {word_id}: {str(e)}",
            exc_info=True,
        )
        return jsonify({"error": "An unexpected server error occurred"}), 500


@words_bp.route("/<word_id>", methods=["DELETE"])
def delete_word(word_id: str):
    """Delete a word associated with the current user."""
    logger.info(
        f"ROUTE: delete_word invoked for word_id: {word_id}, user_id: {g.user_id}"
    )
    try:
        success_data = ws.delete_word_for_user(g.db, g.user_id, word_id)
        logger.info(f"ROUTE: Successfully deleted word {word_id} for user {g.user_id}")
        return jsonify(success_data), 200
    except NotFoundError as e:
        logger.warning(
            f"ROUTE: Word {word_id} not found for user {g.user_id}: {str(e)}"
        )
        return jsonify({"error": str(e)}), e.status_code
    except WordServiceError as e:
        logger.error(
            f"ROUTE: Service error deleting word {word_id} for user {g.user_id}: {str(e)}"
        )
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error deleting word {word_id} for user {g.user_id}: {str(e)}",
            exc_info=True,
        )
        return jsonify({"error": "An unexpected server error occurred"}), 500


@words_bp.route("/<word_id>/star", methods=["POST"])
def star_word(word_id):
    logger.info(
        f"ROUTE: star_word invoked for word_id: {word_id}, user_id: {g.user_id}"
    )
    try:
        success_data = ws.star_word_for_user(g.db, g.user_id, word_id)
        logger.info(f"ROUTE: Successfully starred word {word_id} for user {g.user_id}")
        return jsonify(success_data), 200
    except NotFoundError as e:
        logger.warning(f"ROUTE: Word not found - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except ForbiddenError as e:
        logger.warning(f"ROUTE: Forbidden to star word - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except WordServiceError as e:
        logger.error(f"ROUTE: WordServiceError - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error in star_word for word_id {word_id}: {str(e)}",
            exc_info=True,
        )
        return jsonify({"error": "An unexpected server error occurred"}), 500


@words_bp.route("/<word_id>/descriptions", methods=["POST"])
def add_description_to_word(word_id: str):
    logger.info(
        f"ROUTE: add_description_to_word invoked for word_id: {word_id}, user_id: {g.user_id}"
    )
    try:
        data = request.get_json()
        schema = DescriptionCreateSchema(**data)
        success_data = ws.add_description_for_user(g.db, g.user_id, word_id, schema)
        logger.info(
            f"ROUTE: Successfully added description to word {word_id} for user {g.user_id}"
        )
        return jsonify(success_data), 200
    except (ValidationError, ValueError) as e:
        logger.warning(
            f"ROUTE: Validation error for user {g.user_id} adding description to word {word_id}: {e}"
        )
        return jsonify({"error": f"Invalid input: {e}"}), 400
    except NotFoundError as e:
        logger.warning(f"ROUTE: Word not found - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except ForbiddenError as e:
        logger.warning(f"ROUTE: Forbidden to add a description to word - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except WordServiceError as e:
        logger.error(f"ROUTE: WordServiceError - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error in add_description_to_word for word_id {word_id}: {str(e)}",
            exc_info=True,
        )
        return jsonify({"error": "An unexpected server error occurred"}), 500


@words_bp.route("/<word_id>/descriptions/<description_id>", methods=["PATCH"])
def update_description_in_word(word_id: str, description_id: str):
    logger.info(
        f"ROUTE: update_description_in_word invoked for word_id: {word_id}, description_id: {description_id}, user_id: {g.user_id}"
    )
    try:
        data = request.get_json()
        schema = DescriptionUpdateSchema(**data)
        success_data = ws.update_description_for_user(
            g.db, g.user_id, word_id, description_id, schema.description_text
        )
        logger.info(
            f"ROUTE: Successfully updated description {description_id} in word {word_id} for user {g.user_id}"
        )
        return jsonify(success_data), 200
    except (ValidationError, ValueError) as e:
        logger.warning(
            f"ROUTE: Validation error for user {g.user_id} updating description {description_id}: {e}"
        )
        return jsonify({"error": f"Invalid input: {e}"}), 400
    except NotFoundError as e:
        logger.warning(f"ROUTE: Description not found - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except ForbiddenError as e:
        logger.warning(f"ROUTE: Forbidden to update description - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except WordServiceError as e:
        logger.error(f"ROUTE: WordServiceError - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error in update_description_in_word for word_id {word_id}, description_id {description_id}: {str(e)}",
            exc_info=True,
        )
        return jsonify({"error": "An unexpected server error occurred"}), 500


@words_bp.route("/<word_id>/descriptions/<description_id>", methods=["DELETE"])
def delete_description_from_word(word_id: str, description_id: str):
    logger.info(
        f"ROUTE: delete_description_from_word invoked for word_id: {word_id}, description_id: {description_id}, user_id: {g.user_id}"
    )
    try:
        success_data = ws.delete_description_for_user(
            g.db, g.user_id, word_id, description_id
        )
        logger.info(
            f"ROUTE: Successfully deleted description {description_id} from word {word_id} for user {g.user_id}"
        )
        return jsonify(success_data), 200
    except NotFoundError as e:
        logger.warning(
            f"ROUTE: Description {description_id} not found in word {word_id} for user {g.user_id}: {str(e)}"
        )
        return jsonify({"error": str(e)}), e.status_code
    except WordServiceError as e:
        logger.error(
            f"ROUTE: Service error deleting description {description_id} from word {word_id} for user {g.user_id}: {str(e)}"
        )
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error deleting description {description_id} from word {word_id} for user {g.user_id}: {str(e)}",
            exc_info=True,
        )
        return jsonify({"error": "An unexpected server error occurred"}), 500


@words_bp.route("/<word_id>/examples/<example_id>", methods=["PATCH"])
def update_example_in_word(word_id: str, example_id: str):
    logger.info(
        f"ROUTE: update_example_in_word invoked for word_id: {word_id}, example_id: {example_id}, user_id: {g.user_id}"
    )
    try:
        data = request.get_json()
        schema = ExampleUpdateSchema(**data)
        success_data = ws.update_example_for_user(
            g.db, g.user_id, word_id, example_id, schema.example_text
        )
        logger.info(
            f"ROUTE: Successfully updated example {example_id} in word {word_id} for user {g.user_id}"
        )
        return jsonify(success_data), 200
    except (ValidationError, ValueError) as e:
        logger.warning(
            f"ROUTE: Validation error for user {g.user_id} updating example {example_id}: {e}"
        )
        return jsonify({"error": f"Invalid input: {e}"}), 400
    except NotFoundError as e:
        logger.warning(f"ROUTE: Example not found - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except ForbiddenError as e:
        logger.warning(f"ROUTE: Forbidden to update example - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except WordServiceError as e:
        logger.error(f"ROUTE: WordServiceError - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error in update_example_in_word for word_id {word_id}, example_id {example_id}: {str(e)}",
            exc_info=True,
        )
        return jsonify({"error": "An unexpected server error occurred"}), 500


@words_bp.route("/<word_id>/examples/<example_id>", methods=["DELETE"])
def delete_example_from_word(word_id: str, example_id: str):
    logger.info(
        f"ROUTE: delete_example_from_word invoked for word_id: {word_id}, example_id: {example_id}, user_id: {g.user_id}"
    )
    try:
        success_data = ws.delete_example_for_user(g.db, g.user_id, word_id, example_id)
        logger.info(
            f"ROUTE: Successfully deleted example {example_id} from word {word_id} for user {g.user_id}"
        )
        return jsonify(success_data), 200
    except NotFoundError as e:
        logger.warning(
            f"ROUTE: Example {example_id} not found in word {word_id} for user {g.user_id}: {str(e)}"
        )
        return jsonify({"error": str(e)}), e.status_code
    except WordServiceError as e:
        logger.error(
            f"ROUTE: Service error deleting example {example_id} from word {word_id} for user {g.user_id}: {str(e)}"
        )
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error deleting example {example_id} from word {word_id} for user {g.user_id}: {str(e)}",
            exc_info=True,
        )
        return jsonify({"error": "An unexpected server error occurred"}), 500


@words_bp.route("/<word_id>/examples", methods=["POST"])
def add_example_to_word(word_id: str):
    logger.info(
        f"ROUTE: add_example_to_word invoked for word_id: {word_id}, user_id: {g.user_id}"
    )
    try:
        data = request.get_json()
        schema = ExampleCreateSchema(**data)
        success_data = ws.add_example_for_user(g.db, g.user_id, word_id, schema)
        logger.info(
            f"ROUTE: Successfully added example to word {word_id} for user {g.user_id}"
        )
        return jsonify(success_data), 200
    except (ValidationError, ValueError) as e:
        logger.warning(
            f"ROUTE: Validation error for user {g.user_id} adding example to word {word_id}: {e}"
        )
        return jsonify({"error": f"Invalid input: {e}"}), 400
    except NotFoundError as e:
        logger.warning(f"ROUTE: Word not found - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except ForbiddenError as e:
        logger.warning(f"ROUTE: Forbidden to add an example to word - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except WordServiceError as e:
        logger.error(f"ROUTE: WordServiceError - {str(e)}")
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        logger.error(
            f"ROUTE: Unexpected error in add_example_to_word for word_id {word_id}: {str(e)}",
            exc_info=True,
        )
        return jsonify({"error": "An unexpected server error occurred"}), 500
