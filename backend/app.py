import os
import secrets

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

from backend.src.login_and_create_account.presentation.create_user_presentation import (
    blueprint_create_director_account,)
from backend.src.login_and_create_account.presentation.verify_director_exist_presentation import (
    blueprint_check_director_exists,)   
from backend.src.login_and_create_account.presentation.login_presentation import (
    blueprint_login,)

load_dotenv()

app = Flask(__name__)
jwt_secret_key = os.getenv("JWT_SECRET_KEY")
if jwt_secret_key and len(jwt_secret_key.encode("utf-8")) < 32:
    raise RuntimeError("JWT_SECRET_KEY deve ter pelo menos 32 bytes.")
app.config["JWT_SECRET_KEY"] = jwt_secret_key or secrets.token_urlsafe(48)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
CORS(app, resources={r"/*": {"origins": ["null", "file://"]}})

app.register_blueprint(blueprint_create_director_account)
app.register_blueprint(blueprint_check_director_exists)
app.register_blueprint(blueprint_login)

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
