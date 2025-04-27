import random
import string

import firebase_admin
from firebase_admin import firestore


def generate_random_code(length=8):
    """
    Helper function that generates a random code of 8 characters + numbers.
    """
    characters = string.ascii_uppercase + string.digits
    return "".join(random.choice(characters) for i in range(length))


def _get_firestore_client():
    """
    Gets the Firestore client for the default *already initialized* Firebase app.
    Returns the Firestore client or None on failure.

    """
    try:
        default_app = firebase_admin.get_app()
        print("Default Firebase app already initialized.")
        db = firestore.client(app=default_app)
        print("Firestore client obtained successfully.")
        return db

    except ValueError:
        print("Error: Default Firebase app was not initialized.")
        return None

    except Exception as e:
        print(f"Error getting Firestore client: {e}")
        return None


def _handle_existing_user(user_doc_ref, user_doc, user_name):
    """
    Handles the case where a document exists for the user.
    Retrieves the code, updates name if needed, generates/adds code if missing.
    Returns the user code or None on failure within this step.
    """
    print(f"Document found for UID {user_doc_ref.id} in 'users' collection.")

    user_data = user_doc.to_dict() or {}
    existing_code = user_data.get("code")

    needs_update = False
    data_to_update = {}
    code_to_return = None

    # Check if the provided user_name is different from the stored name (if any)
    stored_name = user_data.get("name")
    if user_name is not None and user_name != stored_name:
        data_to_update["name"] = user_name
        needs_update = True
        print(
            f"Name mismatch for UID {user_doc_ref.id}. Stored: {stored_name}, Provided: {user_name}. Will update name."
        )

    # Check if the code was found in the existing document
    if existing_code is not None:
        # Code was found, this is the code we will return
        code_to_return = existing_code
        print(f"Found existing user code: {existing_code}")
    else:
        # Document exists but the code field is missing.
        print(
            f"Warning: Document for UID {user_doc_ref.id} exists but contains no user code. Generating new."
        )
        needs_update = True
        # Generate a new code
        new_user_code = generate_random_code(8)
        print(f"Generated new user code: {new_user_code}")
        data_to_update["code"] = new_user_code
        code_to_return = new_user_code

    if needs_update:
        data_to_update["updatedAt"] = firestore.SERVER_TIMESTAMP
        try:
            user_doc_ref.update(data_to_update)
            print(f"Updated document for UID {user_doc_ref.id} with: {data_to_update}")
        except Exception as e:
            print(
                f"Error updating document for UID {user_doc_ref.id} with {data_to_update}: {e}"
            )
            return None

    # Return the code we determined (either existing or the new one generated because it was missing)
    return code_to_return


def _handle_new_user(user_doc_ref, user_name):
    """
    Handles the case where a document does not exist for the user.
    Generates a new code, creates the document, and saves initial data.
    Returns the new user code or None on failure within this step.
    """
    print(
        f"Document not found for UID {user_doc_ref.id} in 'users' collection. Generating and saving new code."
    )

    # Generate a new unique code for the user
    new_user_code = generate_random_code(8)
    print(f"Generated new user code: {new_user_code}")

    data_to_save = {
        "user_id": user_doc_ref.id,
        "name": user_name,
        "code": new_user_code,
        "createdAt": firestore.SERVER_TIMESTAMP,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    }

    try:
        user_doc_ref.set(data_to_save)
        print(
            f"Created new document for UID {user_doc_ref.id} in 'users' with code {new_user_code}"
        )
    except Exception as e:
        print(f"Error creating document for UID {user_doc_ref.id}: {e}")
        return None

    return new_user_code


def get_or_create_user_code(uid, user_name):
    """
    Checks Firestore for an existing user code for the given UID.
    If found, returns it. If not, generates a new one and saves it.
    Optionally updates the user's name if different from stored name.
    Returns the user code (string) or None on failure.
    """
    db = _get_firestore_client()
    if db is None:
        print("Failed to obtain Firestore client. Cannot get or create user code.")
        return None

    user_doc_ref = db.collection("users").document(uid)

    try:
        user_doc = user_doc_ref.get()
        print(f"Attempted to get document for UID: {uid}")

        # --- MAIN BRANCHING POINT: Delegate based on document existence ---
        if user_doc.exists:
            # Document exists, call the helper to handle it
            return _handle_existing_user(user_doc_ref, user_doc, user_name)
        else:
            # Document does not exist, call the helper to handle it
            return _handle_new_user(user_doc_ref, user_name)

    except Exception as e:
        # This catch is for errors during the initial .get() operation itself
        print(f"Error during initial document get for UID {uid}: {e}")
        return None
