from backend.configuration.database_connection import DatabaseUnavailable
from backend.src.employees.infrastructure.repository.employee_repository import (
    DuplicateEmployeeData,
    EmployeeBranchNotFound,
    EmployeeRepositoryError,
    create_new_employee,
    get_user_role_by_email,
)
from backend.src.employees.model.employee_model import (
    normalize_employee_role,
    validate_new_employee_data,
)
from backend.src.login_and_create_account.infrastructure.external.password_encryption import (
    hash_password,
)
from backend.src.utils.generate_id import gerar_codigo_aleatorio


def create_new_employee_use_case(data, actor_email):
    normalized, errors = validate_new_employee_data(data)
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
        return {
            "ok": False,
            "message": "Não foi possível validar as permissões do usuário.",
        }, 500

    if not actor or not actor["active"]:
        return {
            "ok": False,
            "message": "Sua conta não tem permissão para cadastrar funcionários.",
        }, 403

    actor_role = normalize_employee_role(actor["role"])
    target_role = normalized["role"]
    if actor_role not in ("diretor", "gerente") or (
        target_role == "diretor" and actor_role != "diretor"
    ):
        return {
            "ok": False,
            "message": "Sua conta não tem permissão para cadastrar este cargo.",
        }, 403

    id_usuario = gerar_codigo_aleatorio()
    id_funcionario = gerar_codigo_aleatorio()
    while id_funcionario == id_usuario:
        id_funcionario = gerar_codigo_aleatorio()

    try:
        password_hash = hash_password(normalized["password"])
        create_new_employee(
            id_usuario=id_usuario,
            id_funcionario=id_funcionario,
            nome=normalized["first_name"],
            sobrenome=normalized["last_name"],
            email=normalized["email"],
            cpf=normalized["cpf"],
            tipo_usuario=target_role,
            password=password_hash,
            codigo_interno=normalized["internal_code"],
            crf=normalized["crf"],
            branch_reference=normalized.get("branch_reference"),
        )
    except DuplicateEmployeeData:
        return {
            "ok": False,
            "message": "Já existe um funcionário com este e-mail, CPF ou código interno.",
        }, 409
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
            "message": "Não foi possível concluir o cadastro. Tente novamente.",
        }, 500

    return {
        "ok": True,
        "message": "Funcionário cadastrado com sucesso.",
        "employee": {
            "id_usuario": id_usuario,
            "id_funcionario": id_funcionario,
            "nome": normalized["first_name"],
            "sobrenome": normalized["last_name"],
            "email": normalized["email"],
            "tipo_usuario": target_role,
            "codigo_interno": normalized["internal_code"],
        },
    }, 201
