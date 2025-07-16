import logging
import os
import sys

import firebase_admin
from firebase_admin import credentials

# --- Flag to prevent multiple initializations ---
_firebase_app_initialized = False


def initialize_firebase_app():
    global _firebase_app_initialized
    # Get logger after logging system is set up
    logger = logging.getLogger("infinite_vocab_app")

    if _firebase_app_initialized:
        logger.info("CONFIG: Firebase Admin SDK already initialized.")
        return

    try:
        if "INFINITE_SECURITY" in os.environ:
            cred_path = os.environ.get("INFINITE_SECURITY")
            logger.info(
                f"CONFIG: Initializing Firebase Admin SDK with credentials from {cred_path}"
            )

            if not os.path.exists(cred_path):
                logger.critical(
                    f"CONFIG: Service account key file not found at {cred_path}"
                )
                sys.exit("Exiting: Missing required service account key.")

            try:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                logger.info("CONFIG: Firebase Admin SDK initialized successfully")

                auth_emulator_host = os.environ.get("FIREBASE_AUTH_EMULATOR_HOST")
                firestore_emulator_host = os.environ.get("FIRESTORE_EMULATOR_HOST")
                using_emulators = auth_emulator_host or firestore_emulator_host

                if using_emulators:
                    logger.info(
                        "CONFIG: Emulator mode detected - connecting to local Firebase emulators"
                    )
                    logger.info(f"CONFIG: Auth emulator: {auth_emulator_host}")
                    logger.info(
                        f"CONFIG: Firestore emulator: {firestore_emulator_host}"
                    )
                else:
                    logger.info(
                        "CONFIG: Production mode - connecting to Firebase Cloud services"
                    )

                _firebase_app_initialized = True

            except ValueError as e:
                if "The default Firebase app already exists" in str(e):
                    logger.info("CONFIG: Firebase Admin SDK already initialized")
                    _firebase_app_initialized = True
                else:
                    logger.critical(
                        f"CONFIG: Firebase initialization failed: {e}", exc_info=True
                    )
                    sys.exit(f"Exiting: Firebase initialization ValueError: {e}")
            except Exception as e:
                logger.critical(
                    f"CONFIG: Firebase initialization failed: {e}", exc_info=True
                )
                sys.exit(f"Exiting: Firebase initialization error: {e}")

        if not _firebase_app_initialized:
            logger.critical("CONFIG: INFINITE_SECURITY environment variable not set")
            logger.critical("CONFIG: Firebase Admin SDK initialization failed")
            sys.exit(
                "Exiting: Firebase environment not configured (INFINITE_SECURITY missing)."
            )

    except Exception as e:
        logger.critical(f"CONFIG: ERROR in Firebase config setup: {e}", exc_info=True)
        sys.exit(f"Exiting: Unexpected error in firebase_config.py: {e}")


initialize_firebase_app()
