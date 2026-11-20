from backend.configuration.database_connection import DatabaseUnavailable
from backend.src.login_and_create_account.infrastructure.external.password_encryption import hash_password
from backend.src.login_and_create_account.infrastructure.repository.director_repository import (
    DirectorRepositoryError,
    DuplicateDirectorData,
    create_new_director,
)
from backend.src.login_and_create_account.model.director_model import (
    normalize_cpf,
    validate_email,
    verify_director_cpf_format,
)
from backend.src.utils.generate_id import gerar_codigo_aleatorio


def use_case_create_account_director(data):
    required_fields = {
        "first_name": "Nome",
        "last_name": "Sobrenome",
        "cpf": "CPF",
        "email": "E-mail",
        "password": "Senha",
        "password_confirmation": "Confirmação de senha",
        "internal_code": "Código interno",
    }
    errors = {}
    normalized = {}
    for key, label in required_fields.items():
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            errors[key] = f"{label} é obrigatório."
        else:
            normalized[key] = value if key in ("password", "password_confirmation") else value.strip()

    if errors:
        return {"ok": False, "message": "Confira os campos obrigatórios.", "errors": errors}, 400

    normalized["email"] = normalized["email"].lower()
    normalized["cpf"] = normalize_cpf(normalized["cpf"])

    if len(normalized["first_name"]) > 100 or len(normalized["last_name"]) > 100:
        errors["name"] = "Nome e sobrenome devem ter no máximo 100 caracteres."
    if not validate_email(normalized["email"]):
        errors["email"] = "Informe um endereço de e-mail válido."
    if not verify_director_cpf_format(normalized["cpf"]):
        errors["cpf"] = "Informe um CPF válido."
    if normalized["password"] != normalized["password_confirmation"]:
        errors["password_confirmation"] = "As senhas não coincidem."
    if len(normalized["password"].encode("utf-8")) > 72:
        errors["password"] = "A senha deve ter no máximo 72 bytes."

    if errors:
        return {"ok": False, "message": "Confira os dados informados.", "errors": errors}, 400


    try:
        password_hash = hash_password(normalized["password"])
        id_usuario = gerar_codigo_aleatorio()
        id_funcional = gerar_codigo_aleatorio()
        while id_funcional == id_usuario:
            id_funcional = gerar_codigo_aleatorio()

        create_new_director(
            id_usuario=id_usuario,
            nome=normalized["first_name"],
            sobrenome=normalized["last_name"],
            email=normalized["email"],
            cpf=normalized["cpf"],
            tipo_usuario="diretor",
            ativo=True,
            id_funcional=id_funcional,
            password=password_hash,
            codigo_interno=normalized["internal_code"],
        )
    except DuplicateDirectorData:
        return {
            "ok": False,
            "message": "Já existe uma conta com este e-mail, CPF ou código interno.",
        }, 409
    except DatabaseUnavailable:
        return {
            "ok": False,
            "message": "Banco de dados indisponível. Tente novamente mais tarde.",
        }, 503
    except DirectorRepositoryError:
        return {
            "ok": False,
            "message": "Não foi possível concluir o cadastro. Tente novamente.",
        }, 500

    return {"ok": True, "message": "Conta do diretor criada com sucesso."}, 201
