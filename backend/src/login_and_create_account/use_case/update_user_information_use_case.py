from backend.configuration.database_connection import DatabaseUnavailable
from backend.src.login_and_create_account.infrastructure.external.password_decryption import (
    verify_password,
)
from backend.src.login_and_create_account.infrastructure.repository.login_repository import (
    LoginRepositoryError,
    find_login_user_by_email,
)
from backend.src.login_and_create_account.infrastructure.repository.user_repository import (
    DuplicateUserData,
    UserNotActive,
    UserNotFound,
    UserRepositoryError,
    update_user_information_by_email,
)
from backend.src.login_and_create_account.model.user_model import (
    profile_response,
    validate_user_profile_update,
)
from backend.src.login_and_create_account.use_case.token_use_case import create_user_token


def update_user_information_use_case(data, actor_email, secret_key):
    normalized, errors = validate_user_profile_update(data, actor_email)
    if errors:
        return {
            "ok": False,
            "message": "Confira os dados informados.",
            "errors": errors,
        }, 400

    email_changed = normalized["email"] != actor_email.strip().lower()
    if email_changed:
        try:
            account = find_login_user_by_email(actor_email.strip().lower())
        except DatabaseUnavailable:
            return {
                "ok": False,
                "message": "Banco de dados indisponível. Tente novamente mais tarde.",
            }, 503
        except LoginRepositoryError:
            return {
                "ok": False,
                "message": "Não foi possível confirmar a identidade do usuário.",
            }, 500

        password_matches = bool(
            account
            and account.get("ativo")
            and verify_password(normalized["current_password"], account.get("senha_funcionario"))
        )
        if not password_matches:
            return {
                "ok": False,
                "message": "Confirme a alteração do e-mail com sua senha atual.",
                "errors": {"current_password": "A senha atual está incorreta."},
            }, 400

    update_data = {
        key: value for key, value in normalized.items() if key != "current_password"
    }

    try:
        user = update_user_information_by_email(actor_email, update_data)
    except DuplicateUserData:
        return {
            "ok": False,
            "message": "Já existe uma conta com este e-mail ou CPF.",
        }, 409
    except (UserNotFound, UserNotActive):
        return {"ok": False, "message": "Sessão inválida ou expirada."}, 401
    except DatabaseUnavailable:
        return {
            "ok": False,
            "message": "Banco de dados indisponível. Tente novamente mais tarde.",
        }, 503
    except UserRepositoryError:
        return {
            "ok": False,
            "message": "Não foi possível atualizar as informações do perfil.",
        }, 500

    token = create_user_token(
        " ".join((normalized["first_name"], normalized["last_name"])),
        normalized["email"],
        secret_key,
    )
    return {
        "ok": True,
        "message": "Informações do perfil atualizadas com sucesso.",
        "user": profile_response(user),
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": 3600,
    }, 200
