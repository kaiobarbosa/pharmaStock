from flask import Blueprint, current_app, jsonify, request
from jwt import InvalidTokenError

from backend.src.employees.use_case.select_all_employee_use_case import (
    select_all_employee_use_case,
    select_employee_by_branch_use_case,
)
from backend.src.login_and_create_account.use_case.token_use_case import (
    decode_user_token,
)


blueprint_select_all_employees = Blueprint(
    "blueprint_select_all_employees", __name__
)


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


def _unauthenticated_response():
    response = jsonify({"ok": False, "message": "Sessão inválida ou expirada."})
    response.headers["Cache-Control"] = "no-store"
    return response, 401


@blueprint_select_all_employees.get("/api/employees")
def select_all_employees():
    actor_email = _authenticated_email()
    if actor_email is None:
        return _unauthenticated_response()

    response_data, status_code = select_all_employee_use_case(actor_email)
    response = jsonify(response_data)
    response.headers["Cache-Control"] = "no-store"
    return response, status_code


@blueprint_select_all_employees.get("/api/employees/branch/<id_filial>")
def select_employees_by_branch(id_filial):
    actor_email = _authenticated_email()
    if actor_email is None:
        return _unauthenticated_response()

    response_data, status_code = select_employee_by_branch_use_case(
        id_filial=id_filial,
        actor_email=actor_email,
    )
    response = jsonify(response_data)
    response.headers["Cache-Control"] = "no-store"
    return response, status_code
