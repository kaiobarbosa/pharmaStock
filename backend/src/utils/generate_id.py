import secrets
import string

from login_and_create_account.infrastructure.repository.verify_id_exist_repository import verify_id_exist

alfabeto = string.ascii_uppercase + string.digits  # A-Z e 0-9


def gerar_codigo_aleatorio(tamanho: int = 6) -> str:
    return "".join(secrets.choice(alfabeto) for _ in range(tamanho))


def gerar_id_usuario_unico() -> str:
    while True:
        codigo_aleatorio = gerar_codigo_aleatorio()
        if not verify_id_exist(codigo_aleatorio):
            return codigo_aleatorio