import os

import firebase_admin
from firebase_admin import credentials

if "INFINITE_SECURITY" in os.environ:
    cred_path = os.environ.get("INFINITE_SECURITY")
    try:
        cred = credentials.Certificate(cred_path)
        firebase_app = firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK initialized successfully!")

    except Exception as e:
        print(f"Error initializing Firebase Admin SDK: {e}")
        print(
            "Please ensure the path in INFINITE_SECURITY is correct and the file is valid."
        )
else:
    print("INFINITE_SECURITY environment variable not set.")
    print("Firebase Admin SDK was NOT initialized.")
    print("You will not be able to use Firebase services in your backend.")
