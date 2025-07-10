"""Admin Service - business logic for admin-only operations."""

from data_access import admin_dal as a_dal
from data_access import user_dal as u_dal
from schemas import RoleUpdateSchema
from utils import AdminServiceError, DatabaseError, DuplicateEntryError, NotFoundError


def get_all_users(db):
    """Retrieves a list of all users, enriching each with their admin status."""
    try:
        admin_ids = a_dal.get_all_admin_ids(db)
        all_users = u_dal.list_all_users(db)
        for user in all_users:
            if user.user_id in admin_ids:
                user.is_admin = True
        return all_users
    except DatabaseError as e:
        raise AdminServiceError("Failed to retrieve all users from database.") from e


def add_admin_privileges(db, user_id_to_promote: str, current_admin_id: str):
    """Promotes a regular user to an admin."""

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
        return {
            "message": f"User '{user_to_promote.user_name}' has been promoted to admin."
        }
    except (NotFoundError, DuplicateEntryError):
        raise
    except DatabaseError as e:
        raise AdminServiceError("A database error occurred during promotion.") from e


def update_admin_role(db, user_id_to_update: str, schema: RoleUpdateSchema):
    """Updates the role for a user who is already an admin."""
    try:
        admin_ids = a_dal.get_all_admin_ids(db)
        if user_id_to_update not in admin_ids:
            raise NotFoundError("Cannot update role: User is not an admin.")

        a_dal.update_admin_role(db, user_id_to_update, schema.role)
        return {"message": f"Admin role updated to '{schema.role}'."}
    except NotFoundError:
        raise
    except DatabaseError as e:
        raise AdminServiceError("A database error occurred while updating role.") from e


def remove_admin_privileges(db, user_id_to_demote: str):
    """Demotes an admin back to a regular user."""
    try:
        admin_ids = a_dal.get_all_admin_ids(db)
        if user_id_to_demote not in admin_ids:
            raise NotFoundError("Cannot demote: User is not an admin.")

        a_dal.demote_admin(db, user_id_to_demote)
        return {"message": "Admin privileges have been revoked."}
    except NotFoundError:
        raise
    except DatabaseError as e:
        raise AdminServiceError("A database error occurred during demotion.") from e
