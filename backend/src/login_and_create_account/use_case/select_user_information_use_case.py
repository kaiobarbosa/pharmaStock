from backend.configuration.database_connection import DatabaseUnavailable
from backend.src.login_and_create_account.infrastructure.repository.user_repository import (
    UserNotActive,
    UserNotFound,
    UserRepositoryError,
    select_user_information_by_email,
)
from backend.src.login_and_create_account.model.user_model import profile_response


def select_user_information_use_case(actor_email):
    try:
        user = select_user_information_by_email(actor_email)
    except DatabaseUnavailable:
        return {
            "ok": False,
            "message": "Banco de dados indisponível. Tente novamente mais tarde.",
        }, 503
    except (UserNotFound, UserNotActive):
        return {"ok": False, "message": "Sessão inválida ou expirada."}, 401
    except UserRepositoryError:
        return {
            "ok": False,
            "message": "Não foi possível carregar as informações do perfil.",
        }, 500

    if not user or not user.get("active"):
        return {"ok": False, "message": "Sessão inválida ou expirada."}, 401
    return {"ok": True, "user": profile_response(user)}, 200
