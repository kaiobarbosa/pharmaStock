import os

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

from backend.src.login_and_create_account.presentation.create_user_presentation import (
    blueprint_create_director_account,
)

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["null", "file://"]}})
app.register_blueprint(blueprint_create_director_account)


@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "pharmastock-api"}), 200


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.getenv("FLASK_PORT", "5000")),
        debug=False,
        use_reloader=False,
        threaded=True,
    )
