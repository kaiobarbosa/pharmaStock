import bcrypt

from backend.configuration.database_connection import DatabaseUnavailable
from backend.src.login_and_create_account.infrastructure.external.password_decryption import (
    verify_password,
)
from backend.src.login_and_create_account.infrastructure.repository.login_repository import (
    LoginRepositoryError,
    find_login_user_by_email,
)
from backend.src.login_and_create_account.model.director_model import validate_email
from backend.src.login_and_create_account.model.login_model import verify_user_null_fields
from backend.src.login_and_create_account.use_case.token_use_case import create_user_token

_DUMMY_PASSWORD_HASH = bcrypt.hashpw(b"invalid-login-placeholder", bcrypt.gensalt()).decode(
    "utf-8"
)


def login_user(email, password, secret_key):
    if not verify_user_null_fields(email, password):
        return {"ok": False, "message": "Informe um e-mail e uma senha válidos."}, 400

    email = email.strip().lower()
    try:
        email.encode("utf-8")
        password_size = len(password.encode("utf-8"))
    except UnicodeEncodeError:
        return {"ok": False, "message": "E-mail ou senha inválidos."}, 401
    if len(email) > 254 or not validate_email(email) or password_size > 72:
        return {"ok": False, "message": "E-mail ou senha inválidos."}, 401

    try:
        user = find_login_user_by_email(email)
    except DatabaseUnavailable:
        return {
            "ok": False,
            "message": "Banco de dados indisponível. Tente novamente mais tarde.",
        }, 503
    except LoginRepositoryError:
        return {
            "ok": False,
            "message": "Não foi possível concluir o login. Tente novamente.",
        }, 500

    # Use the same response for unknown, inactive, and incorrect-password accounts
    # to avoid disclosing whether an email is registered.
    invalid_credentials = {"ok": False, "message": "E-mail ou senha inválidos."}
    password_hash = user["senha_funcionario"] if user else _DUMMY_PASSWORD_HASH
    password_matches = verify_password(password, password_hash)
    if not user or not user["ativo"] or not password_matches:
        return invalid_credentials, 401

    full_name = " ".join(
        part.strip()
        for part in (user["nome_usuario"], user["sobrenome_usuario"])
        if part and part.strip()
    )
    token = create_user_token(full_name, user["email_usuario"], secret_key)
    return {
        "ok": True,
        "message": "Login realizado com sucesso.",
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": 3600,
    }, 200
