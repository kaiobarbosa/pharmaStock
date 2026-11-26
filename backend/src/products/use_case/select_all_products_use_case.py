from backend.configuration.database_connection import DatabaseUnavailable
from backend.src.employees.infrastructure.repository.employee_repository import (
    EmployeeRepositoryError,
    get_user_role_by_email,
)
from backend.src.employees.model.employee_model import normalize_employee_role
from backend.src.products.infrastructure.repository.select_all_products import (
    ProductListingRepositoryError,
    select_all_products,
)


def select_all_products_use_case(actor_email):
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
            "message": "Sua conta não tem acesso à listagem de produtos.",
        }, 403

    try:
        products = select_all_products()
    except DatabaseUnavailable:
        return {
            "ok": False,
            "message": "Banco de dados indisponível. Tente novamente mais tarde.",
        }, 503
    except ProductListingRepositoryError:
        return {
            "ok": False,
            "message": "Não foi possível carregar os produtos. Tente novamente.",
        }, 500

    return {"ok": True, "products": products}, 200
