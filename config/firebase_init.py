import logging
import os
import sys

import firebase_admin
from firebase_admin import credentials

logger = logging.getLogger("infinite_vocab_app")

# --- Flag to prevent multiple initializations ---
_firebase_app_initialized = False


def initialize_firebase_app():
    global _firebase_app_initialized
    if _firebase_app_initialized:
        logger.info("CONFIG: Firebase Admin SDK already initialized.")
        return

    try:
        if "INFINITE_SECURITY" in os.environ:
            cred_path = os.environ.get("INFINITE_SECURITY")
            logger.info("CONFIG: --------------------------------------------------")
            logger.info(
                f"CONFIG: CREDENTIAL DETECTED: Attempting initialization using: {cred_path}"
            )

            if not os.path.exists(cred_path):
                logger.critical(
                    f"CONFIG: Service account key file not found at {cred_path}"
                )
                logger.critical("CONFIG: Firebase Admin SDK NOT initialized.")
                logger.critical(
                    "CONFIG: --------------------------------------------------"
                )
                sys.exit("Exiting: Missing required service account key.")

            try:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                logger.info(
                    "CONFIG: Firebase Admin SDK initialized successfully using credentials!"
                )

                auth_emulator_host = os.environ.get("FIREBASE_AUTH_EMULATOR_HOST")
                firestore_emulator_host = os.environ.get("FIRESTORE_EMULATOR_HOST")
                using_emulators = auth_emulator_host or firestore_emulator_host

                if using_emulators:
                    logger.info(
                        "CONFIG: --------------------------------------------------"
                    )
                    logger.info(
                        "CONFIG: NOTE: Emulator host variables ALSO detected. SDK will connect to emulators."
                    )
                    logger.info(f"CONFIG: Auth Host: {auth_emulator_host}")
                    logger.info(f"CONFIG: Firestore Host: {firestore_emulator_host}")
                    logger.info(
                        "CONFIG: --------------------------------------------------"
                    )
                else:
                    logger.info(
                        "CONFIG: --------------------------------------------------"
                    )
                    logger.info(
                        "CONFIG: NOTE: No emulator host variables detected. SDK will connect to Cloud."
                    )
                    logger.info(
                        "CONFIG: --------------------------------------------------"
                    )

                _firebase_app_initialized = True

            except ValueError as e:
                if "The default Firebase app already exists" in str(e):
                    logger.info(
                        "CONFIG: Firebase Admin SDK was already initialized (caught ValueError)."
                    )
                    _firebase_app_initialized = True
                else:
                    logger.critical(
                        f"CONFIG: ERROR during Firebase Admin SDK initialization (ValueError): {e}",
                        exc_info=True,
                    )
                    sys.exit(f"Exiting: Firebase initialization ValueError: {e}")
            except Exception as e:
                logger.critical(
                    f"CONFIG: ERROR during Firebase Admin SDK initialization: {e}",
                    exc_info=True,
                )
                sys.exit(f"Exiting: Firebase initialization error: {e}")

        if not _firebase_app_initialized:
            logger.warning("CONFIG: --------------------------------------------------")
            logger.warning(
                "CONFIG: WARNING: INFINITE_SECURITY environment variable not set."
            )
            logger.warning("CONFIG: Firebase Admin SDK was NOT initialized.")
            logger.warning(
                "CONFIG: You will NOT be able to connect to Firebase services."
            )
            logger.warning("CONFIG: --------------------------------------------------")
            sys.exit(
                "Exiting: Firebase environment not configured (INFINITE_SECURITY missing)."
            )

    except Exception as e:
        logger.critical(f"CONFIG: ERROR in Firebase config setup: {e}", exc_info=True)
        sys.exit(f"Exiting: Unexpected error in firebase_config.py: {e}")


initialize_firebase_app()
