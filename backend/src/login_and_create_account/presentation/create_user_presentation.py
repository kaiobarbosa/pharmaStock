from flask import Blueprint, jsonify, request

from backend.src.login_and_create_account.use_case.create_account_use_case import (
    use_case_create_account_director,
)

blueprint_create_director_account = Blueprint(
    "blueprint_create_director_account", __name__
)


@blueprint_create_director_account.post("/api/create_director_account")
@blueprint_create_director_account.post("/create_director_account")
def create_director_account():
    if not request.is_json:
        return jsonify({"ok": False, "message": "O corpo deve estar em formato JSON."}), 415

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"ok": False, "message": "O corpo JSON enviado é inválido."}), 400

    response_data, status_code = use_case_create_account_director(data)
    return jsonify(response_data), status_code
