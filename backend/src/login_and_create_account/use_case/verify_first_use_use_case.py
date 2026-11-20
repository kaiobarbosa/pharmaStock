from backend.configuration.database_connection import DatabaseUnavailable
from backend.src.login_and_create_account.infrastructure.repository.verify_id_exist_repository import (
    verify_director_exist,
)

def verify_first_use() -> tuple[dict, int]:

    try:
        existe_diretor = verify_director_exist()
        return {
            "director_exists": existe_diretor,
            "requires_initial_setup": not existe_diretor,
        }, 200

    except DatabaseUnavailable:
        return {"ok": False, "message": "Banco de dados indisponível."}, 503
    except Exception:
        return {"ok": False, "message": "Falha ao verificar o primeiro acesso."}, 500
