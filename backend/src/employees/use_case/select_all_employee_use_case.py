from backend.configuration.database_connection import DatabaseUnavailable
from backend.src.employees.infrastructure.repository.employee_repository import (
    EmployeeRepositoryError,
    get_user_role_by_email,
    select_all_employees,
    select_employees_by_branch,
)
from backend.src.employees.model.employee_model import (
    normalize_branch_id,
    normalize_employee_role,
)


def _authorize_employee_listing(actor_email):
    try:
        actor = get_user_role_by_email(actor_email)
    except DatabaseUnavailable:
        return None, (
            {
                "ok": False,
                "message": "Banco de dados indisponível. Tente novamente mais tarde.",
            },
            503,
        )
    except EmployeeRepositoryError:
        return None, (
            {"ok": False, "message": "Não foi possível validar a sessão."},
            500,
        )

    if (
        not actor
        or not actor["active"]
        or normalize_employee_role(actor["role"]) is None
    ):
        return None, (
            {"ok": False, "message": "Sua conta não tem acesso à listagem de funcionários."},
            403,
        )

    return True, None


def select_all_employee_use_case(actor_email):
    authorized, error_response = _authorize_employee_listing(actor_email)
    if not authorized:
        return error_response

    try:
        employees = select_all_employees()
    except DatabaseUnavailable:
        return {
            "ok": False,
            "message": "Banco de dados indisponível. Tente novamente mais tarde.",
        }, 503
    except EmployeeRepositoryError:
        return {
            "ok": False,
            "message": "Não foi possível carregar os funcionários.",
        }, 500

    return {"ok": True, "employees": employees}, 200


def select_employee_by_branch_use_case(id_filial, actor_email):
    normalized_branch_id = normalize_branch_id(id_filial)
    if normalized_branch_id is None:
        return {"ok": False, "message": "Identificador de filial inválido."}, 400

    authorized, error_response = _authorize_employee_listing(actor_email)
    if not authorized:
        return error_response

    try:
        employees = select_employees_by_branch(normalized_branch_id)
    except DatabaseUnavailable:
        return {
            "ok": False,
            "message": "Banco de dados indisponível. Tente novamente mais tarde.",
        }, 503
    except EmployeeRepositoryError:
        return {
            "ok": False,
            "message": "Não foi possível carregar os funcionários da filial.",
        }, 500

    return {"ok": True, "employees": employees}, 200
