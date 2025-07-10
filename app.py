from flask import Flask

from config import firebase_init  # noqa: F401
from routes import category_bp, search_bp, user_bp, word_category_bp, words_bp
from utils import camelized_response

app = Flask(__name__)
app.register_blueprint(user_bp)
app.register_blueprint(words_bp)
app.register_blueprint(category_bp)
app.register_blueprint(word_category_bp)
app.register_blueprint(search_bp)


@app.route("/")
def root_info():
    return camelized_response(
        {
            "message": "Welcome to the Infinite Vocabulary API!",
            "version": "v1.0",
            "status": "healthy",
        },
        200,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
