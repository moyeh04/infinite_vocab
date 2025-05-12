import os
import sys

import firebase_admin
from firebase_admin import credentials

# --- Flag to prevent multiple initializations ---
_firebase_app_initialized = False


def initialize_firebase_app():
    global _firebase_app_initialized
    if _firebase_app_initialized:
        print("Firebase Admin SDK already initialized.")
        return

    try:
        if "INFINITE_SECURITY" in os.environ:
            cred_path = os.environ.get("INFINITE_SECURITY")
            print("--------------------------------------------------")
            print(
                f"CREDENTIAL DETECTED: Attempting initialization using: {cred_path}"
            )

            if not os.path.exists(cred_path):
                print(
                    f"ERROR: Service account key file not found at {cred_path}"
                )
                print("Firebase Admin SDK NOT initialized.")
                print("--------------------------------------------------")
                sys.exit("Exiting: Missing required service account key.")

            try:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                print(
                    "Firebase Admin SDK initialized successfully using credentials!"
                )

                auth_emulator_host = os.environ.get(
                    "FIREBASE_AUTH_EMULATOR_HOST"
                )
                firestore_emulator_host = os.environ.get(
                    "FIRESTORE_EMULATOR_HOST"
                )
                using_emulators = auth_emulator_host or firestore_emulator_host

                if using_emulators:
                    print("--------------------------------------------------")
                    print(
                        "NOTE: Emulator host variables ALSO detected. SDK will connect to emulators."
                    )
                    print(f"Auth Host: {auth_emulator_host}")
                    print(f"Firestore Host: {firestore_emulator_host}")
                    print("--------------------------------------------------")
                else:
                    print("--------------------------------------------------")
                    print(
                        "NOTE: No emulator host variables detected. SDK will connect to Cloud."
                    )
                    print("--------------------------------------------------")

                _firebase_app_initialized = True

            except ValueError as e:
                if "The default Firebase app already exists" in str(e):
                    print(
                        "Firebase Admin SDK was already initialized (caught ValueError)."
                    )
                    _firebase_app_initialized = True
                else:
                    print(
                        f"ERROR during Firebase Admin SDK initialization (ValueError): {e}"
                    )
                    sys.exit(
                        f"Exiting: Firebase initialization ValueError: {e}"
                    )
            except Exception as e:
                print(f"ERROR during Firebase Admin SDK initialization: {e}")
                sys.exit(f"Exiting: Firebase initialization error: {e}")

        if not _firebase_app_initialized:
            print("--------------------------------------------------")
            print("WARNING: INFINITE_SECURITY environment variable not set.")
            print("Firebase Admin SDK was NOT initialized.")
            print("You will NOT be able to connect to Firebase services.")
            print("--------------------------------------------------")
            sys.exit(
                "Exiting: Firebase environment not configured (INFINITE_SECURITY missing)."
            )

    except Exception as e:
        print(f"ERROR in Firebase config setup: {e}")
        sys.exit(f"Exiting: Unexpected error in firebase_config.py: {e}")


initialize_firebase_app()
