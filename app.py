from flask import Flask, jsonify

from config import firebase_init  # noqa: F401
from routes.user_routes import user_bp
from routes.word_routes import words_bp

app = Flask(__name__)
app.register_blueprint(user_bp)
app.register_blueprint(words_bp)


@app.route("/")
def root_info():
    return jsonify(
        {
            "message": "Welcome to the Infinite Vocabulary API!",
            "version": "v1.0",
            "status": "healthy",
            # "documentation": "/api/docs"
        }
    ), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)
