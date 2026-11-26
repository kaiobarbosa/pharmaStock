from mysql.connector import Error, IntegrityError

from backend.configuration.database_connection import conectar_banco


class UserRepositoryError(Exception):
    """Raised when profile data cannot be read or updated."""


class UserNotFound(Exception):
    """Raised when the authenticated account no longer exists."""


class UserNotActive(Exception):
    """Raised when the authenticated account has been disabled."""


class DuplicateUserData(Exception):
    """Raised when another account already uses the email or CPF."""


_PROFILE_SELECT = """
    SELECT u.id_usuario AS id_usuario,
           u.nome_usuario AS first_name,
           u.sobrenome_usuario AS last_name,
           u.email_usuario AS email,
           u.cpf_usuario AS cpf,
           u.tipo_usuario AS role,
           u.ativo AS active,
           f.codigo_interno AS internal_code,
           f.crf_funcionario AS crf,
           COALESCE(fil.nome_filial, f.id_filial) AS branch
    FROM usuario AS u
    INNER JOIN funcionario AS f ON f.id_usuario = u.id_usuario
    LEFT JOIN filial AS fil ON fil.id_filial = f.id_filial
"""


def select_user_information_by_email(email):
    """Load the signed-in employee's profile by the email in their token."""
    connection = None
    cursor = None
    try:
        connection = conectar_banco()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            _PROFILE_SELECT + " WHERE u.email_usuario = %s LIMIT 1",
            (email,),
        )
        return cursor.fetchone()
    except Error as error:
        raise UserRepositoryError from error
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


def update_user_information_by_email(current_email, data):
    """Update only personal profile fields for the token's account."""
    connection = None
    cursor = None
    try:
        connection = conectar_banco()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            _PROFILE_SELECT
            + " WHERE u.email_usuario = %s LIMIT 1 FOR UPDATE",
            (current_email,),
        )
        user = cursor.fetchone()
        if user is None:
            raise UserNotFound
        if not user["active"]:
            raise UserNotActive

        cursor.execute(
            """
            SELECT 1
            FROM usuario
            WHERE email_usuario = %s AND id_usuario <> %s
            LIMIT 1
            """,
            (data["email"], user["id_usuario"]),
        )
        if cursor.fetchone():
            raise DuplicateUserData

        cursor.execute(
            """
            SELECT 1
            FROM usuario
            WHERE cpf_usuario = %s AND id_usuario <> %s
            LIMIT 1
            """,
            (data["cpf"], user["id_usuario"]),
        )
        if cursor.fetchone():
            raise DuplicateUserData

        cursor.execute(
            """
            UPDATE usuario
            SET nome_usuario = %s,
                sobrenome_usuario = %s,
                email_usuario = %s,
                cpf_usuario = %s
            WHERE id_usuario = %s
            """,
            (
                data["first_name"],
                data["last_name"],
                data["email"],
                data["cpf"],
                user["id_usuario"],
            ),
        )
        # Keep the employee's email record aligned with the account email.
        cursor.execute(
            "UPDATE funcionario SET email_verificado = %s WHERE id_usuario = %s",
            (data["email"], user["id_usuario"]),
        )
        connection.commit()

        user.update(data)
        return user
    except (UserNotFound, UserNotActive, DuplicateUserData):
        if connection is not None:
            connection.rollback()
        raise
    except IntegrityError as error:
        if connection is not None:
            connection.rollback()
        if error.errno == 1062:
            raise DuplicateUserData from error
        raise UserRepositoryError from error
    except Error as error:
        if connection is not None:
            connection.rollback()
        raise UserRepositoryError from error
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
