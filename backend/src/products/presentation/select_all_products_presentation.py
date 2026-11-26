from flask import Blueprint, current_app, jsonify, request
from jwt import InvalidTokenError

from backend.src.login_and_create_account.use_case.token_use_case import (
    decode_user_token,
)
from backend.src.products.use_case.select_all_products_use_case import (
    select_all_products_use_case,
)


blueprint_select_all_products = Blueprint("blueprint_select_all_products", __name__)


@blueprint_select_all_products.get("/api/products")
@blueprint_select_all_products.get("/api/select_all_products")
def select_products():
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        response = jsonify({"ok": False, "message": "Sessão inválida ou expirada."})
        response.headers["Cache-Control"] = "no-store"
        return response, 401

    try:
        claims = decode_user_token(token.strip(), current_app.config["JWT_SECRET_KEY"])
    except InvalidTokenError:
        response = jsonify({"ok": False, "message": "Sessão inválida ou expirada."})
        response.headers["Cache-Control"] = "no-store"
        return response, 401

    actor_email = claims.get("email")
    if not isinstance(actor_email, str) or not actor_email.strip():
        response = jsonify({"ok": False, "message": "Sessão inválida ou expirada."})
        response.headers["Cache-Control"] = "no-store"
        return response, 401

    response_data, status_code = select_all_products_use_case(actor_email.strip())
    response = jsonify(response_data)
    response.headers["Cache-Control"] = "no-store"
    return response, status_code
