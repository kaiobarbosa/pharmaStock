from mysql.connector import Error, IntegrityError

from backend.configuration.database_connection import conectar_banco


class DuplicateBranchData(Exception):
    """Raised when a generated branch or address identifier already exists."""


class BranchRepositoryError(Exception):
    """Raised when a branch and its address cannot be stored."""


def create_new_branch(
    id_filial,
    nome_filial,
    id_endereco,
    cep,
    logradouro,
    numero,
    complemento,
    bairro,
    cidade,
    estado,
):
    connection = conectar_banco()

    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO endereco
                    (id_endereco, logradouro, numero, complemento, bairro, cidade, estado, cep)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    id_endereco,
                    logradouro,
                    numero,
                    complemento or "",
                    bairro,
                    cidade,
                    estado,
                    cep,
                ),
            )
            cursor.execute(
                """
                INSERT INTO filial (id_filial, nome_filial, id_endereco)
                VALUES (%s, %s, %s)
                """,
                (id_filial, nome_filial, id_endereco),
            )
            connection.commit()
        finally:
            cursor.close()
    except IntegrityError as error:
        connection.rollback()
        if error.errno == 1062:
            raise DuplicateBranchData from error
        raise BranchRepositoryError from error
    except Error as error:
        connection.rollback()
        raise BranchRepositoryError from error
    finally:
        connection.close()

    return True


def get_all_branches():
    connection = conectar_banco()

    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT f.id_filial, f.nome_filial, e.id_endereco, e.cep,
                       e.logradouro, e.numero, e.complemento, e.bairro,
                       e.cidade, e.estado
                FROM filial AS f
                INNER JOIN endereco AS e ON e.id_endereco = f.id_endereco
                ORDER BY f.nome_filial ASC
                """
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()
    except Error as error:
        raise BranchRepositoryError from error
    finally:
        connection.close()

    return [
        {
            "id_filial": row[0],
            "nome_filial": row[1],
            "id_endereco": row[2],
            "cep": row[3],
            "logradouro": row[4],
            "numero": row[5],
            "complemento": row[6],
            "bairro": row[7],
            "cidade": row[8],
            "estado": row[9],
        }
        for row in rows
    ]


