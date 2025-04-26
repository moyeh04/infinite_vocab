import random
import string

import firebase_admin
from firebase_admin import exceptions, firestore  # noqa: F401


def generate_random_code(length=8):
    """
    Generates a random code of 8 characters + numbers.
    """
    characters = string.ascii_lowercase + string.digits

    return "".join(random.choice(characters) for i in range(length))


def _get_firestore_client():
    """
    Gets the Firestore client for the default Firebase app.
    Initializes the default app if it hasn't been already.
    Returns the Firestore client or None on failure.
    """
    try:
        default_app = firebase_admin.get_app()
        db = firestore.client(app=default_app)
        print("Firestore client obtained successfully in user_service.py")
        return db

    except ValueError:
        print("Default Firebase app not initialized. Cannot get Firestore client.")
        return None

    except Exception as e:
        print(f"Error getting Firestore client: {e}")
        return None


def get_or_create_user_code(uid, user_name):
    """
    Checks Firestore for an existing user code for the given UID.
    If found, returns it. If not, generates a new one and saves it.
    Returns the user code or None on failure.
    """
    db = _get_firestore_client()
    if db is None:
        print("Failed to obtain Firestore client. Cannot get or create user code.")
        return None

    user_doc_ref = db.collection("users").document(uid)

    try:
        code_exists = True  # Just an assumption for the code to work
        user_doc = user_doc_ref.get()
        print(f"Attempted to get document for UID: {uid}")

        # Login Logic
        if user_doc.exists:
            user_data = user_doc.to_dict()

            if user_data and "name" in user_data:
                if user_name == user_data["name"]:
                    user_data_to_update = {
                        "name": user_name,
                    }
                    user_doc_ref.update(user_data_to_update)

            if user_data and "code" in user_data:
                existing_code = user_data["code"]
                print(
                    f"Document for UID {uid} found in 'users' collection. Found existing user code: {existing_code}"
                )
                return existing_code

            else:
                code_exists = False
                print(
                    f"Warning: Document for UID {uid} exists in 'users' collection but contains no user code. Generating new."
                )

        # Signup Logic
        # Generate a new unique code for the user
        new_user_code = generate_random_code(8)
        print(f"Generated new user code: {new_user_code}")
        if code_exists:
            # This means that user data exists so we don't want to over write it again
            user_data_to_update = {
                "code": new_user_code,
            }
            user_doc_ref.update(user_data_to_update)
        else:
            print(
                f"Document for UID {uid} not found or incomplete in 'users' collection. Generating and saving new code."
            )
            user_data_to_save = {
                "user_id": uid,
                "name": user_name,
                "code": new_user_code,
                "createdAt": firestore.SERVER_TIMESTAMP,
            }
            user_doc_ref.set(user_data_to_save)

        print(
            f"Saved new document for UID {uid} in 'users' collection with code {new_user_code}"
        )

        return new_user_code

    except Exception as e:
        print(f"Error processing document for UID {uid} in 'users' collection: {e}")
        return None
