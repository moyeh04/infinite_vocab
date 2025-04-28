from firebase_admin import auth
from flask import Flask, jsonify, request

import firebase_config  # noqa: F401
from routes.word_routes import words_bp
from services.user_service import get_or_create_user_code as usr_code

app = Flask(__name__)
app.register_blueprint(words_bp, url_prefix="/api/v1/words")


@app.route("/")
def hello_world():
    print("Route '/' was called!")
    return "<p>Hello, Backend World!<h1>test1</h1></p>"


@app.route("/authenticate", methods=["POST"])
def authenticate_user():
    id_token = request.json.get("idToken")
    user_name = request.json.get("name")

    if not id_token:
        return jsonify({"error": "ID token not provided"}), 400

    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token["uid"]
        print(f"Successfully authenticated user with UID: {uid}")

        # --- Call the user service to get or create the user's application code ---
        user_code = usr_code(uid, user_name)

        # --- Check if the user service returned a valid code ---
        if user_code is None:
            # If the service function returned None, it means there was an error getting/creating the code
            print(f"Error: Failed to get or create user code for UID {uid}.")
            # Return a 500 Internal Server Error to indicate a server-side problem
            return jsonify({"error": "Failed to retrieve or create user data"}), 500

        return jsonify(
            {
                "message": "User authenticated successfully",
                "uid": uid,
                "name": user_name,
                "userCode": user_code,
            }
        ), 200

    except ValueError:
        print("Error: Invalid ID token provided.")
        return jsonify({"error": "Invalid ID token"}), 401

    except Exception as e:
        print(f"Error verifying ID token: {e}")
        return jsonify({"error": "Failed to authenticate user"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
