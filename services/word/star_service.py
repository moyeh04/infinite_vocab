"""Star service - Clean milestone logic following category service pattern"""

import logging

from data_access import word_dal as w_dal
from factories import WordFactory
from utils import DatabaseError, NotFoundError, ForbiddenError, WordServiceError

logger = logging.getLogger("infinite_vocab_app")


def star_word_for_user(db, user_id: str, word_id: str) -> dict:
    """Stars a word and checks for milestone prompts - clean and focused"""
    logger.info(
        f"SERVICE: star_word_for_user invoked for word '{word_id}' by user '{user_id}'."
    )
    try:
        # Use atomic transaction like the original
        transaction = db.transaction()
        atomic_result = w_dal.atomic_update(transaction, db, word_id, user_id)

        if atomic_result == "NOT_FOUND":
            raise NotFoundError(f"Word with ID '{word_id}' not found.")
        elif atomic_result == "FORBIDDEN":
            raise ForbiddenError("You are not authorized to modify this word.")

        new_star_count, word_text = atomic_result

        # Use WordFactory for milestone validation - clean business logic
        milestone_prompts = WordFactory.validate_star_milestones(new_star_count)

        logger.info(
            f"SERVICE: Star updated for word ID '{word_id}' (text: '{word_text}') for user_id: {user_id}. New stars: {new_star_count}"
        )

        return {
            "message": f"Successfully starred word '{word_text}'.",
            "word_id": word_id,
            "new_star_count": new_star_count,
            "prompt_for_description": milestone_prompts["prompt_for_description"],
            "prompt_for_example": milestone_prompts["prompt_for_example"],
        }

    except (NotFoundError, ForbiddenError):
        raise
    except DatabaseError as e:
        logger.error(f"SERVICE: DatabaseError starring word ID '{word_id}': {str(e)}")
        raise WordServiceError(
            "A database problem occurred while starring the word."
        ) from e
    except Exception as e:
        logger.error(
            f"SERVICE: Unexpected error starring word ID '{word_id}': {str(e)}",
            exc_info=True,
        )
        raise WordServiceError(
            "An unexpected service error occurred while starring the word."
        ) from e


def check_milestone_prompts(star_count: int) -> dict:
    """Checks if star count triggers milestone prompts - utility function"""
    return WordFactory.validate_star_milestones(star_count)
