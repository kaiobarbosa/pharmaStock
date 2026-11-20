import os

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

from backend.src.login_and_create_account.presentation.create_user_presentation import (
    blueprint_create_director_account,)
from backend.src.login_and_create_account.presentation.verify_director_exist_presentation import (
    blueprint_check_director_exists,)   

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["null", "file://"]}})
app.register_blueprint(blueprint_create_director_account)
app.register_blueprint(blueprint_check_director_exists)


@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "pharmastock-api"}), 200


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.getenv("FLASK_PORT", "5055")),
        debug=False,
        use_reloader=False,
        threaded=True,
    )
