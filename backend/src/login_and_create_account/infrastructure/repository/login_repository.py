from mysql.connector import Error

from backend.configuration.database_connection import conectar_banco


class LoginRepositoryError(Exception):
    """Raised when the login query cannot be completed."""


def find_login_user_by_email(email):
    """Return the account identity and password hash associated with an email."""
    connection = None
    cursor = None
    try:
        connection = conectar_banco()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT u.nome_usuario, u.sobrenome_usuario, u.email_usuario,
                   u.ativo, f.senha_funcionario
            FROM usuario AS u
            INNER JOIN funcionario AS f ON f.id_usuario = u.id_usuario
            WHERE LOWER(u.email_usuario) = %s
            LIMIT 1
            """,
            (email.lower(),),
        )
        return cursor.fetchone()
    except Error as error:
        raise LoginRepositoryError from error
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
