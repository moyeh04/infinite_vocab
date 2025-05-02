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
        # Check if running with Emulators
        auth_emulator_host = os.environ.get("FIREBASE_AUTH_EMULATOR_HOST")
        firestore_emulator_host = os.environ.get("FIRESTORE_EMULATOR_HOST")
        using_emulators = auth_emulator_host or firestore_emulator_host

        if using_emulators:
            # Emulator Mode
            print("--------------------------------------------------")
            print("EMULATOR DETECTED: Initializing Firebase Admin SDK for Emulators.")

            print(f"Auth Host: {auth_emulator_host}")
            print(f"Firestore Host: {firestore_emulator_host}")

            # Initialize without credentials for emulators.
            firebase_admin.initialize_app()
            print("Firebase Admin SDK initialized for Emulator use.")
            print("--------------------------------------------------")

        elif "INFINITE_SECURITY" in os.environ:
            # Cloud Mode (Credentials Provided)
            cred_path = os.environ.get("INFINITE_SECURITY")

            print("--------------------------------------------------")
            print(
                f"CLOUD MODE: Initializing Firebase Admin SDK with credentials from: {cred_path}"
            )
            if not os.path.exists(cred_path):
                print(f"ERROR: Service account key file not found at {cred_path}")
                print("Firebase Admin SDK NOT initialized.")
                print("--------------------------------------------------")
                sys.exit("Exiting: Missing required service account key.")
                # return

            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized successfully for Cloud use!")
            print("--------------------------------------------------")

        else:
            # Neither Emulators nor Credentials Configured
            print("--------------------------------------------------")
            print(
                "WARNING: Neither Firebase Emulator environment variables nor INFINITE_SECURITY are set."
            )
            print("Firebase Admin SDK was NOT initialized.")

            print(
                "You will NOT be able to connect to Firebase services (Cloud or Emulator)."
            )
            print("--------------------------------------------------")
            sys.exit("Exiting: Firebase environment not configured.")
            # return

        _firebase_app_initialized = True  # Mark as initialized successfully

    except ValueError as e:
        # Handles case where initialize_app() might be called again somehow
        if "The default Firebase app already exists" in str(e):
            print("Firebase Admin SDK was already initialized.")
            _firebase_app_initialized = True  # Ensure flag is set
        else:
            print(f"ERROR during Firebase Admin SDK initialization: {e}")
            sys.exit(f"Exiting: Firebase initialization error: {e}")
    except Exception as e:
        print(f"ERROR during Firebase Admin SDK initialization: {e}")
        sys.exit(f"Exiting: Firebase initialization error: {e}")


initialize_firebase_app()
