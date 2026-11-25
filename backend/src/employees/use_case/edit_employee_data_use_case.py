from backend.configuration.database_connection import DatabaseUnavailable
from backend.src.employees.infrastructure.repository.employee_repository import (
    DuplicateEmployeeData,
    EmployeeBranchNotFound,
    EmployeeEditConflict,
    EmployeeNotFound,
    EmployeeRepositoryError,
    get_employee_role_by_email,
    get_user_role_by_email,
    update_employee_data,
)
from backend.src.employees.model.employee_model import (
    normalize_employee_role,
    validate_employee_edit_data,
)
from backend.src.login_and_create_account.model.director_model import validate_email


def edit_employee_data_use_case(current_email, data, actor_email):
    if not isinstance(current_email, str) or not validate_email(current_email.strip()):
        return {"ok": False, "message": "E-mail atual do funcionário inválido."}, 400
    current_email = current_email.strip().lower()

    normalized, errors = validate_employee_edit_data(data)
    if errors:
        return {
            "ok": False,
            "message": "Confira os dados informados.",
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
        return {"ok": False, "message": "Não foi possível validar as permissões."}, 500

    if not actor or not actor["active"]:
        return {"ok": False, "message": "Sua conta não tem permissão para editar funcionários."}, 403

    actor_role = normalize_employee_role(actor["role"])
    if actor_role not in ("diretor", "gerente"):
        return {"ok": False, "message": "Sua conta não tem permissão para editar funcionários."}, 403

    try:
        employee = get_employee_role_by_email(current_email)
    except DatabaseUnavailable:
        return {
            "ok": False,
            "message": "Banco de dados indisponível. Tente novamente mais tarde.",
        }, 503
    except EmployeeRepositoryError:
        return {"ok": False, "message": "Não foi possível localizar o funcionário."}, 500

    if not employee:
        return {"ok": False, "message": "Funcionário não encontrado."}, 404

    current_role = normalize_employee_role(employee["role"])
    if current_role is None:
        return {"ok": False, "message": "O cargo atual do funcionário é inválido."}, 409

    target_role = normalized["role"]
    if target_role == "farmaceutico" and current_role != "farmaceutico" and normalized["crf"] is None:
        return {
            "ok": False,
            "message": "Confira os dados informados.",
            "errors": {"crf": "CRF é obrigatório para farmacêuticos."},
        }, 400
    if actor_role == "gerente" and (
        current_role == "diretor" or target_role == "diretor"
    ):
        return {
            "ok": False,
            "message": "Gerentes não podem editar diretores nem promover funcionários a diretor.",
        }, 403

    try:
        update_employee_data(
            current_email=current_email,
            expected_current_role=employee["role"],
            nome=normalized["first_name"],
            sobrenome=normalized["last_name"],
            email=normalized["email"],
            tipo_usuario=target_role,
            crf=normalized["crf"],
            branch_reference=normalized.get("branch_reference"),
        )
    except EmployeeNotFound:
        return {"ok": False, "message": "Funcionário não encontrado."}, 404
    except EmployeeEditConflict:
        return {
            "ok": False,
            "message": "Os dados do funcionário mudaram. Recarregue a tela e tente novamente.",
        }, 409
    except DuplicateEmployeeData:
        return {"ok": False, "message": "Já existe um funcionário com este e-mail."}, 409
    except EmployeeBranchNotFound:
        return {"ok": False, "message": "A filial selecionada não foi encontrada."}, 404
    except DatabaseUnavailable:
        return {
            "ok": False,
            "message": "Banco de dados indisponível. Tente novamente mais tarde.",
        }, 503
    except EmployeeRepositoryError:
        return {
            "ok": False,
            "message": "Não foi possível atualizar o funcionário. Tente novamente.",
        }, 500

    return {"ok": True, "message": "Funcionário atualizado com sucesso."}, 200
