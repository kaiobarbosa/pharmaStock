import secrets
import string


_ID_ALPHABET = string.ascii_uppercase + string.digits


def gerar_codigo_aleatorio(tamanho=6):
    return "".join(secrets.choice(_ID_ALPHABET) for _ in range(tamanho))


def gerar_id_usuario_unico():
    # The database unique constraint remains the final collision guard.
    return gerar_codigo_aleatorio()
