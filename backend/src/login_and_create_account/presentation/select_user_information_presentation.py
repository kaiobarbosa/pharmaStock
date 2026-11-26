from flask import Blueprint, current_app, jsonify, request
from jwt import InvalidTokenError

from backend.src.login_and_create_account.use_case.select_user_information_use_case import (
    select_user_information_use_case,
)
from backend.src.login_and_create_account.use_case.token_use_case import decode_user_token


blueprint_select_user_information = Blueprint(
    "blueprint_select_user_information", __name__
)


def _json_response(data, status_code):
    response = jsonify(data)
    response.headers["Cache-Control"] = "no-store"
    return response, status_code


@blueprint_select_user_information.get("/api/users/me")
def select_user_information():
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return _json_response(
            {"ok": False, "message": "Sessão inválida ou expirada."}, 401
        )

    try:
        claims = decode_user_token(token.strip(), current_app.config["JWT_SECRET_KEY"])
    except InvalidTokenError:
        return _json_response(
            {"ok": False, "message": "Sessão inválida ou expirada."}, 401
        )

    actor_email = claims.get("email")
    if not isinstance(actor_email, str) or not actor_email.strip():
        return _json_response(
            {"ok": False, "message": "Sessão inválida ou expirada."}, 401
        )

    result, status_code = select_user_information_use_case(actor_email.strip())
    return _json_response(result, status_code)
