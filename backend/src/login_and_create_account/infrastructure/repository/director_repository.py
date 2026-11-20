from mysql.connector import Error, IntegrityError

from backend.configuration.database_connection import conectar_banco


class DuplicateDirectorData(Exception):
    """Raised when email, CPF, or internal code already belongs to an account."""


class DirectorRepositoryError(Exception):
    """Raised when a director record cannot be stored."""


def create_new_director(
    id_usuario,
    nome,
    sobrenome,
    email,
    cpf,
    tipo_usuario,
    ativo,
    id_funcional,
    password,
    codigo_interno,
):
    if tipo_usuario != "diretor":
        raise DirectorRepositoryError("Este repositório aceita apenas contas de diretor.")

    id_filial = "Diretoria"
    connection = conectar_banco()

    try:

       
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT 1 FROM usuario
                WHERE email_usuario = %s OR cpf_usuario = %s
                LIMIT 1
                """,
                (email, cpf),
            )
            if cursor.fetchone():
                raise DuplicateDirectorData

            cursor.execute(
                "SELECT 1 FROM funcionario WHERE codigo_interno = %s LIMIT 1",
                (codigo_interno,),
            )
            if cursor.fetchone():
                raise DuplicateDirectorData

            cursor.execute(
                """
                INSERT INTO usuario
                    (id_usuario, nome_usuario, sobrenome_usuario, email_usuario,
                     cpf_usuario, tipo_usuario, ativo, criado_em)
                VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                """,
                (id_usuario, nome, sobrenome, email, cpf, tipo_usuario, ativo),
            )
            cursor.execute(
                """
                INSERT INTO funcionario
                    (id_funcionario, senha_funcionario, email_verificado,
                     id_filial, crf_funcionario, codigo_interno, id_usuario)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (id_funcional, password, False, id_filial, "N/A", codigo_interno, id_usuario),
            )
            connection.commit()
        finally:
            cursor.close()
    except DuplicateDirectorData:
        connection.rollback()
        raise
    except IntegrityError as error:
        connection.rollback()
        if error.errno == 1062:
            raise DuplicateDirectorData from error
        raise DirectorRepositoryError from error
    except Error as error:
        connection.rollback()
        raise DirectorRepositoryError from error
    finally:
        connection.close()

    return True


def verify_director_exists(codigo_interno):
    connection = conectar_banco()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM funcionario WHERE codigo_interno = %s LIMIT 1",
                (codigo_interno,),
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()
    finally:
        connection.close()


def verify_director_email_exists(email):
    connection = conectar_banco()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM usuario WHERE email_usuario = %s LIMIT 1", (email,)
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()
    finally:
        connection.close()
