from flask import Blueprint, current_app, jsonify, request
from jwt import InvalidTokenError

from backend.src.login_and_create_account.use_case.token_use_case import (
    decode_user_token,
)
from backend.src.products.use_case.create_new_product_use_case import (
    create_new_product_use_case,
)


blueprint_create_product = Blueprint("blueprint_create_product", __name__)


def _json_response(data, status_code):
    response = jsonify(data)
    response.headers["Cache-Control"] = "no-store"
    return response, status_code


@blueprint_create_product.post("/api/products")
@blueprint_create_product.post("/api/create_product")
@blueprint_create_product.post("/create_product")
def create_product():
    if not request.is_json:
        return _json_response(
            {"ok": False, "message": "O corpo deve estar em formato JSON."}, 415
        )

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _json_response(
            {"ok": False, "message": "O corpo JSON enviado é inválido."}, 400
        )

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

    response_data, status_code = create_new_product_use_case(data, actor_email.strip())
    return _json_response(response_data, status_code)
