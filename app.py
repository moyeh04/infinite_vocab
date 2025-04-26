from firebase_admin import auth
from flask import Flask, request

import firebase_config  # noqa: F401
from services.user_service import get_or_create_user_code as usr_code

app = Flask(__name__)


@app.route("/")
def hello_world():
    print("Route '/' was called!")
    return "<p>Hello, Backend World!<h1>test1</h1></p>"


@app.route("/authenticate", methods=["POST"])
def authenticate_user():
    id_token = request.json.get("idToken")
    user_name = request.json.get("name")
    if not id_token:
        return {"error": "ID token not provided"}, 400
    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token["uid"]
        print(f"Successfully authenticated user with UID: {uid}")
        user_code = usr_code(uid, user_name)
        return {
            "message": "User authenticated successfully",
            "user_id": uid,
            "name": user_name,
            "code": user_code,
        }, 200

    except ValueError:
        return {"error": "Invalid ID token"}, 401
    except Exception as e:
        print(f"Error verifying ID token: {e}")
        return {"error": "Failed to authenticate user"}, 500


if __name__ == "__main__":
    app.run(debug=True)
