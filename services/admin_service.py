"""Admin Service - business logic for admin-only operations."""

import logging
from typing import List

from data_access import admin_dal as a_dal
from data_access import admin_student_dal as as_dal
from data_access import user_dal as u_dal
from models import User
from schemas import RoleUpdateSchema
from utils import AdminServiceError, DatabaseError, DuplicateEntryError, NotFoundError

logger = logging.getLogger("infinite_vocab_app")


def get_all_users(db):
    """Retrieves a list of all users, enriching each with their admin status."""
    logger.info("SERVICE: get_all_users invoked.")
    try:
        admin_ids = a_dal.get_all_admin_ids(db)
        all_users = u_dal.list_all_users(db)
        logger.info(
            f"SERVICE: Found {len(all_users)} total users and {len(admin_ids)} admins."
        )
        for user in all_users:
            if user.user_id in admin_ids:
                user.is_admin = True
        return all_users
    except DatabaseError as e:
        logger.error(f"SERVICE: DatabaseError in get_all_users: {e}")
        raise AdminServiceError("Failed to retrieve all users from database.") from e


def add_admin_privileges(db, user_id_to_promote: str, current_admin_id: str):
    """Promotes a regular user to an admin."""
    logger.info(
        f"SERVICE: Admin {current_admin_id} attempting to promote {user_id_to_promote}."
    )
    try:
        user_to_promote = u_dal.get_user_by_id(db, user_id_to_promote)
        if not user_to_promote:
            raise NotFoundError(f"User with ID '{user_id_to_promote}' not found.")

        admin_ids = a_dal.get_all_admin_ids(db)
        if user_id_to_promote in admin_ids:
            raise DuplicateEntryError(
                f"User '{user_to_promote.user_name}' is already an admin."
            )

        a_dal.promote_user_to_admin(db, user_id_to_promote, current_admin_id)
        logger.info(
            f"SERVICE: User {user_id_to_promote} successfully promoted by {current_admin_id}."
        )
        return {
            "message": f"User '{user_to_promote.user_name}' has been promoted to admin."
        }
    except (NotFoundError, DuplicateEntryError) as e:
        logger.warning(
            f"SERVICE: Pre-condition failed for admin {current_admin_id} promoting {user_id_to_promote}: {e}"
        )
        raise
    except DatabaseError as e:
        logger.error(f"SERVICE: DatabaseError promoting {user_id_to_promote}: {e}")
        raise AdminServiceError("A database error occurred during promotion.") from e


def update_admin_role(db, user_id_to_update: str, schema: RoleUpdateSchema):
    """Updates the role for a user who is already an admin."""
    logger.info(
        f"SERVICE: Attempting to update role for admin {user_id_to_update} to '{schema.role}'."
    )
    try:
        admin_ids = a_dal.get_all_admin_ids(db)
        if user_id_to_update not in admin_ids:
            raise NotFoundError("Cannot update role: User is not an admin.")

        a_dal.update_admin_role(db, user_id_to_update, schema.role)
        logger.info(
            f"SERVICE: Successfully updated role for admin {user_id_to_update}."
        )
        return {"message": f"Admin role updated to '{schema.role}'."}
    except NotFoundError as e:
        logger.warning(
            f"SERVICE: Attempt to update role for non-admin user {user_id_to_update} failed: {e}"
        )
        raise
    except DatabaseError as e:
        logger.error(
            f"SERVICE: DatabaseError updating role for admin {user_id_to_update}: {e}"
        )
        raise AdminServiceError("A database error occurred while updating role.") from e


def remove_admin_privileges(db, user_id_to_demote: str):
    """Demotes an admin back to a regular user."""
    logger.info(f"SERVICE: Attempting to demote admin {user_id_to_demote}.")
    try:
        admin_ids = a_dal.get_all_admin_ids(db)
        if user_id_to_demote not in admin_ids:
            raise NotFoundError("Cannot demote: User is not an admin.")

        a_dal.demote_admin(db, user_id_to_demote)
        logger.info(f"SERVICE: Successfully demoted admin {user_id_to_demote}.")

        return {"message": "Admin privileges have been revoked."}
    except NotFoundError as e:
        logger.warning(
            f"SERVICE: Attempt to demote non-admin user {user_id_to_demote} failed: {e}"
        )
        raise
    except DatabaseError as e:
        logger.error(f"SERVICE: DatabaseError demoting admin {user_id_to_demote}: {e}")
        raise AdminServiceError("A database error occurred during demotion.") from e


def assign_student_to_admin(db, admin_id: str, student_id_to_assign: str) -> dict:
    """Assigns a student to the requesting admin, enforcing business rules."""
    logger.info(
        f"SERVICE: Admin {admin_id} attempting to assign student {student_id_to_assign}."
    )
    try:
        # Rule 1: Ensure the student exists as a user.
        student = u_dal.get_user_by_id(db, student_id_to_assign)
        if not student:
            raise NotFoundError(
                f"User with ID '{student_id_to_assign}' does not exist."
            )

        # Rule 2: Ensure the user being assigned is not another admin.
        all_admin_ids = a_dal.get_all_admin_ids(db)
        if student_id_to_assign in all_admin_ids:
            raise DuplicateEntryError("Cannot assign an admin as a student.")

        # Rule 3: Ensure the student is not already assigned to another admin.
        existing_link = as_dal.get_link_by_student_id(db, student_id_to_assign)
        if existing_link:
            if existing_link.get("admin_id") == admin_id:
                raise DuplicateEntryError(
                    f"User '{student.user_name}' is already assigned to you."
                )
            else:
                raise DuplicateEntryError(
                    f"User '{student.user_name}' is already assigned to another admin."
                )

        # If all checks pass, create the link.

        as_dal.create_link(db, admin_id, student_id_to_assign)
        logger.info(
            f"SERVICE: Successfully assigned student {student_id_to_assign} to admin {admin_id}."
        )
        return {"message": f"Successfully assigned student '{student.user_name}'."}

    except (NotFoundError, DuplicateEntryError) as e:
        logger.warning(
            f"SERVICE: Pre-condition failed for admin {admin_id} assigning student {student_id_to_assign}: {e}"
        )
        raise
    except DatabaseError as e:
        logger.error(
            f"SERVICE: DatabaseError assigning student {student_id_to_assign} to admin {admin_id}: {e}"
        )
        raise AdminServiceError(
            "A database error occurred while assigning the student."
        ) from e


def remove_student_from_admin(db, admin_id: str, student_id_to_remove: str) -> dict:
    """Removes a student from an admin's management, checking ownership."""
    logger.info(
        f"SERVICE: Admin {admin_id} attempting to remove student {student_id_to_remove}."
    )
    try:
        # Check if the student is currently assigned to this admin.
        existing_link = as_dal.get_link_by_student_id(db, student_id_to_remove)
        if not existing_link or existing_link.get("admin_id") != admin_id:
            raise NotFoundError("This student is not assigned to you.")

        # If the link exists and is correct, remove it.
        as_dal.remove_link(db, admin_id, student_id_to_remove)
        logger.info(
            f"SERVICE: Successfully removed student {student_id_to_remove} from admin {admin_id}."
        )

        return {"message": "Successfully removed student."}

    except NotFoundError as e:
        logger.warning(
            f"SERVICE: NotFound error for admin {admin_id} removing student {student_id_to_remove}: {e}"
        )
        raise
    except DatabaseError as e:
        logger.error(
            f"SERVICE: DatabaseError removing student {student_id_to_remove} from admin {admin_id}: {e}"
        )
        raise AdminServiceError(
            "A database error occurred while removing the student."
        ) from e


def list_students_for_admin(db, admin_id: str) -> List[User]:
    """Lists all students assigned to the currently logged-in admin."""
    logger.info(f"SERVICE: Listing students for admin {admin_id}.")
    try:
        student_ids = as_dal.get_students_for_admin(db, admin_id)
        if not student_ids:
            return []

        # Fetch the full user object for each student ID
        student_users = [
            u_dal.get_user_by_id(db, student_id) for student_id in student_ids
        ]
        # Filter out any None results in case a user was deleted but the link remained
        return [user for user in student_users if user is not None]

    except DatabaseError as e:
        logger.error(
            f"SERVICE: DatabaseError listing students for admin {admin_id}: {e}"
        )
        raise AdminServiceError(
            "A database error occurred while listing students."
        ) from e
