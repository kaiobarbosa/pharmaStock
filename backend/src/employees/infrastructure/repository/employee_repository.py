from mysql.connector import Error, IntegrityError

from backend.configuration.database_connection import conectar_banco


class DuplicateEmployeeData(Exception):
    """Raised when an employee email, CPF, or internal code is already in use."""


class EmployeeBranchNotFound(Exception):
    """Raised when the selected branch does not exist."""


class EmployeeRepositoryError(Exception):
    """Raised when employee data cannot be read or stored."""


_EMPLOYEE_LIST_SELECT = """
    SELECT u.nome_usuario AS nome,
           u.sobrenome_usuario AS sobrenome,
           u.tipo_usuario AS tipo_usuario,
           COALESCE(fil.nome_filial, f.id_filial) AS filial,
           u.email_usuario AS email
    FROM funcionario AS f
    INNER JOIN usuario AS u ON u.id_usuario = f.id_usuario
    LEFT JOIN filial AS fil ON fil.id_filial = f.id_filial
"""
_EMPLOYEE_LIST_FIELDS = ("nome", "sobrenome", "tipo_usuario", "filial", "email")


def _select_employees(where_clause="", params=()):
    connection = conectar_banco()
    try:
        cursor = connection.cursor()
        try:
            query = _EMPLOYEE_LIST_SELECT
            if where_clause:
                query += f" WHERE {where_clause}"
            query += " ORDER BY u.nome_usuario ASC, u.sobrenome_usuario ASC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
        finally:
            cursor.close()
    except Error as error:
        raise EmployeeRepositoryError from error
    finally:
        connection.close()

    return [dict(zip(_EMPLOYEE_LIST_FIELDS, row)) for row in rows]


def select_all_employees():
    return _select_employees()


def select_employees_by_branch(id_filial):
    return _select_employees("f.id_filial = %s", (id_filial,))


def get_user_role_by_email(email):
    connection = conectar_banco()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT tipo_usuario, ativo
                FROM usuario
                WHERE LOWER(email_usuario) = LOWER(%s)
                LIMIT 1
                """,
                (email,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return {"role": row[0], "active": bool(row[1])}
        finally:
            cursor.close()
    except Error as error:
        raise EmployeeRepositoryError from error
    finally:
        connection.close()


def create_new_employee(
    id_usuario,
    id_funcionario,
    nome,
    sobrenome,
    email,
    cpf,
    tipo_usuario,
    password,
    codigo_interno,
    crf,
    branch_reference=None,
):
    connection = conectar_banco()

    try:
        cursor = connection.cursor()
        try:
            id_filial = "Diretoria"
            if tipo_usuario != "diretor":
                cursor.execute(
                    """
                    SELECT id_filial
                    FROM filial
                    WHERE id_filial = %s OR LOWER(nome_filial) = LOWER(%s)
                    LIMIT 1
                    """,
                    (branch_reference, branch_reference),
                )
                branch_row = cursor.fetchone()
                if branch_row is None:
                    raise EmployeeBranchNotFound
                id_filial = branch_row[0]

            cursor.execute(
                """
                SELECT 1 FROM usuario
                WHERE LOWER(email_usuario) = LOWER(%s) OR cpf_usuario = %s
                LIMIT 1
                """,
                (email, cpf),
            )
            if cursor.fetchone():
                raise DuplicateEmployeeData

            cursor.execute(
                "SELECT 1 FROM funcionario WHERE codigo_interno = %s LIMIT 1",
                (codigo_interno,),
            )
            if cursor.fetchone():
                raise DuplicateEmployeeData

            cursor.execute(
                """
                INSERT INTO usuario
                    (id_usuario, nome_usuario, sobrenome_usuario, email_usuario,
                     cpf_usuario, tipo_usuario, ativo, criado_em)
                VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                """,
                (id_usuario, nome, sobrenome, email, cpf, tipo_usuario, True),
            )
            cursor.execute(
                """
                INSERT INTO funcionario
                    (id_funcionario, senha_funcionario, email_verificado,
                     id_filial, crf_funcionario, codigo_interno, id_usuario)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    id_funcionario,
                    password,
                    email,
                    id_filial,
                    crf,
                    codigo_interno,
                    id_usuario,
                ),
            )

            if tipo_usuario != "diretor":
                cursor.execute(
                    "INSERT INTO usuario_filial (id_usuario, id_filial) VALUES (%s, %s)",
                    (id_usuario, id_filial),
                )

            connection.commit()
        finally:
            cursor.close()
    except (DuplicateEmployeeData, EmployeeBranchNotFound):
        connection.rollback()
        raise
    except IntegrityError as error:
        connection.rollback()
        if error.errno == 1062:
            raise DuplicateEmployeeData from error
        raise EmployeeRepositoryError from error
    except Error as error:
        connection.rollback()
        raise EmployeeRepositoryError from error
    finally:
        connection.close()

    return True
