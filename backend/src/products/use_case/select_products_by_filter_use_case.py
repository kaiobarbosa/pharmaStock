from backend.configuration.database_connection import DatabaseUnavailable
from backend.src.employees.infrastructure.repository.employee_repository import (
    EmployeeRepositoryError,
    get_user_role_by_email,
)
from backend.src.employees.model.employee_model import normalize_employee_role
from backend.src.products.infrastructure.repository.select_all_products import (
    ProductListingRepositoryError,
)
from backend.src.products.infrastructure.repository.select_products_by_filter_repository import (
    select_products_by_filter,
)
from backend.src.products.model.products_model import validate_product_search_filters


def _search_products(query, branch_id, actor_email, *, require_query=False):
    normalized, errors = validate_product_search_filters(
        query=query,
        branch_id=branch_id,
        require_query=require_query,
        require_filter=True,
    )
    if errors:
        return {
            "ok": False,
            "message": "Confira os filtros informados.",
            "errors": errors,
        }, 400

    try:
        actor = get_user_role_by_email(actor_email)
    except DatabaseUnavailable:
        return {
            "ok": False,
            "message": "Banco de dados indisponível. Tente novamente mais tarde.",
        }, 503
    except EmployeeRepositoryError:
        return {"ok": False, "message": "Não foi possível validar a sessão."}, 500

    if (
        not actor
        or not actor["active"]
        or normalize_employee_role(actor["role"]) is None
    ):
        return {
            "ok": False,
            "message": "Sua conta não tem acesso à pesquisa de produtos.",
        }, 403

    try:
        products = select_products_by_filter(
            query=normalized.get("query"),
            branch_id=normalized.get("branch_id"),
        )
    except DatabaseUnavailable:
        return {
            "ok": False,
            "message": "Banco de dados indisponível. Tente novamente mais tarde.",
        }, 503
    except ProductListingRepositoryError:
        return {
            "ok": False,
            "message": "Não foi possível pesquisar os produtos. Tente novamente.",
        }, 500

    return {"ok": True, "products": products}, 200


def search_products_by_text_use_case(query, actor_email):
    return _search_products(query, None, actor_email, require_query=True)


def select_products_by_filter_use_case(query, branch_id, actor_email):
    return _search_products(query, branch_id, actor_email)
