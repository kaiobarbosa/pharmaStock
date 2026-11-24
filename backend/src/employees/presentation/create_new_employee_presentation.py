from flask import Blueprint, current_app, jsonify, request
from jwt import InvalidTokenError

from backend.src.employees.use_case.create_new_employee_use_case import (
    create_new_employee_use_case,
)
from backend.src.login_and_create_account.use_case.token_use_case import (
    decode_user_token,
)


blueprint_create_employee = Blueprint("blueprint_create_employee", __name__)


@blueprint_create_employee.post("/api/employees")
@blueprint_create_employee.post("/api/create_employee")
@blueprint_create_employee.post("/create_employee")
def create_employee():
    if not request.is_json:
        return jsonify({"ok": False, "message": "O corpo deve estar em formato JSON."}), 415

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"ok": False, "message": "O corpo JSON enviado é inválido."}), 400

    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return jsonify({"ok": False, "message": "Sessão inválida ou expirada."}), 401

    try:
        claims = decode_user_token(token.strip(), current_app.config["JWT_SECRET_KEY"])
    except InvalidTokenError:
        return jsonify({"ok": False, "message": "Sessão inválida ou expirada."}), 401

    actor_email = claims.get("email")
    if not isinstance(actor_email, str) or not actor_email.strip():
        return jsonify({"ok": False, "message": "Sessão inválida ou expirada."}), 401

    response_data, status_code = create_new_employee_use_case(data, actor_email.strip())
    response = jsonify(response_data)
    response.headers["Cache-Control"] = "no-store"
    return response, status_code
