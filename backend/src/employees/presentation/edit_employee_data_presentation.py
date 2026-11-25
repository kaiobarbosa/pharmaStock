from flask import Blueprint, current_app, jsonify, request
from jwt import InvalidTokenError

from backend.src.employees.use_case.edit_employee_data_use_case import (
    edit_employee_data_use_case,
)
from backend.src.login_and_create_account.use_case.token_use_case import (
    decode_user_token,
)


blueprint_edit_employee = Blueprint("blueprint_edit_employee", __name__)


def _authenticated_email():
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None

    try:
        claims = decode_user_token(token.strip(), current_app.config["JWT_SECRET_KEY"])
    except InvalidTokenError:
        return None

    email = claims.get("email")
    if not isinstance(email, str) or not email.strip():
        return None
    return email.strip()


@blueprint_edit_employee.put("/api/employees/email/<path:current_email>")
def edit_employee(current_email):
    actor_email = _authenticated_email()
    if actor_email is None:
        response = jsonify({"ok": False, "message": "Sessão inválida ou expirada."})
        response.headers["Cache-Control"] = "no-store"
        return response, 401

    if not request.is_json:
        return jsonify({"ok": False, "message": "O corpo deve estar em formato JSON."}), 415

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"ok": False, "message": "O corpo JSON enviado é inválido."}), 400

    response_data, status_code = edit_employee_data_use_case(
        current_email=current_email,
        data=data,
        actor_email=actor_email,
    )
    response = jsonify(response_data)
    response.headers["Cache-Control"] = "no-store"
    return response, status_code
