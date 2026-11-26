from flask import Blueprint, current_app, jsonify, request
from jwt import InvalidTokenError

from backend.src.login_and_create_account.use_case.token_use_case import (
    decode_user_token,
)
from backend.src.products.use_case.select_products_by_filter_use_case import (
    search_products_by_text_use_case,
    select_products_by_filter_use_case,
)


blueprint_select_products_by_filter = Blueprint(
    "blueprint_select_products_by_filter", __name__
)


def _json_response(data, status_code):
    response = jsonify(data)
    response.headers["Cache-Control"] = "no-store"
    return response, status_code


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


def _single_query_parameter(name):
    values = request.args.getlist(name)
    if len(values) > 1:
        return None, False
    return (values[0] if values else None), True


@blueprint_select_products_by_filter.get("/api/products/search")
def search_products_by_text():
    actor_email = _authenticated_email()
    if actor_email is None:
        return _json_response(
            {"ok": False, "message": "Sessão inválida ou expirada."}, 401
        )

    query, query_is_unique = _single_query_parameter("query")
    if not query_is_unique:
        return _json_response(
            {"ok": False, "message": "Informe apenas um texto de pesquisa."}, 400
        )

    response_data, status_code = search_products_by_text_use_case(query, actor_email)
    return _json_response(response_data, status_code)


@blueprint_select_products_by_filter.get("/api/products/filter")
def select_products_by_filter():
    actor_email = _authenticated_email()
    if actor_email is None:
        return _json_response(
            {"ok": False, "message": "Sessão inválida ou expirada."}, 401
        )

    query, query_is_unique = _single_query_parameter("query")
    branch_id, branch_is_unique = _single_query_parameter("branch_id")
    if not query_is_unique or not branch_is_unique:
        return _json_response(
            {"ok": False, "message": "Os filtros devem ser informados uma única vez."}, 400
        )

    response_data, status_code = select_products_by_filter_use_case(
        query=query,
        branch_id=branch_id,
        actor_email=actor_email,
    )
    return _json_response(response_data, status_code)
