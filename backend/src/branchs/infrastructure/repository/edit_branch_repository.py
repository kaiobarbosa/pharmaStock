from mysql.connector import Error, IntegrityError

from backend.configuration.database_connection import conectar_banco


class DuplicateBranchEditData(Exception):
    """Raised when an address identifier conflicts with an existing record."""


class BranchEditRepositoryError(Exception):
    """Raised when a branch and its address cannot be updated."""


def update_branch_data(
    id_filial,
    nome_filial,
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
                "SELECT id_endereco FROM filial WHERE id_filial = %s FOR UPDATE",
                (id_filial,),
            )
            branch_row = cursor.fetchone()
            if not branch_row:
                connection.rollback()
                return None

            id_endereco = branch_row[0]
            cursor.execute(
                """
                UPDATE endereco
                SET logradouro = %s, numero = %s, complemento = %s,
                    bairro = %s, cidade = %s, estado = %s, cep = %s
                WHERE id_endereco = %s
                """,
                (
                    logradouro,
                    numero,
                    complemento or "",
                    bairro,
                    cidade,
                    estado,
                    cep,
                    id_endereco,
                ),
            )
            cursor.execute(
                "UPDATE filial SET nome_filial = %s WHERE id_filial = %s",
                (nome_filial, id_filial),
            )
            connection.commit()
        finally:
            cursor.close()
    except IntegrityError as error:
        connection.rollback()
        if error.errno == 1062:
            raise DuplicateBranchEditData from error
        raise BranchEditRepositoryError from error
    except Error as error:
        connection.rollback()
        raise BranchEditRepositoryError from error
    finally:
        connection.close()

    return {"id_endereco": id_endereco}
