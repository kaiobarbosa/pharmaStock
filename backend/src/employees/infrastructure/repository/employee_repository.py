from mysql.connector import Error, IntegrityError

from backend.configuration.database_connection import conectar_banco


class DuplicateEmployeeData(Exception):
    """Raised when an employee email, CPF, or internal code is already in use."""


class EmployeeBranchNotFound(Exception):
    """Raised when the selected branch does not exist."""


class EmployeeRepositoryError(Exception):
    """Raised when employee data cannot be read or stored."""


class EmployeeNotFound(Exception):
    """Raised when the employee being edited does not exist."""


class EmployeeEditConflict(Exception):
    """Raised when an employee changed after it was loaded for editing."""


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


def get_employee_role_by_email(email):
    connection = conectar_banco()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT u.tipo_usuario
                FROM usuario AS u
                INNER JOIN funcionario AS f ON f.id_usuario = u.id_usuario
                WHERE LOWER(u.email_usuario) = LOWER(%s)
                LIMIT 1
                """,
                (email,),
            )
            row = cursor.fetchone()
            return {"role": row[0]} if row else None
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


def update_employee_data(
    current_email,
    expected_current_role,
    nome,
    sobrenome,
    email,
    tipo_usuario,
    crf,
    branch_reference=None,
):
    connection = conectar_banco()

    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT u.id_usuario, u.tipo_usuario, f.id_filial
                FROM usuario AS u
                INNER JOIN funcionario AS f ON f.id_usuario = u.id_usuario
                WHERE LOWER(u.email_usuario) = LOWER(%s)
                LIMIT 1
                FOR UPDATE
                """,
                (current_email,),
            )
            employee_row = cursor.fetchone()
            if employee_row is None:
                raise EmployeeNotFound
            id_usuario, current_role, current_id_filial = employee_row
            if current_role != expected_current_role:
                raise EmployeeEditConflict

            cursor.execute(
                """
                SELECT 1 FROM usuario
                WHERE LOWER(email_usuario) = LOWER(%s) AND id_usuario <> %s
                LIMIT 1
                """,
                (email, id_usuario),
            )
            if cursor.fetchone():
                raise DuplicateEmployeeData

            is_existing_director = str(current_role).strip().lower() in ("diretor", "director")
            preserve_director_branch = tipo_usuario == "diretor" and is_existing_director
            id_filial = current_id_filial if preserve_director_branch else "Diretoria"
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
                UPDATE usuario
                SET nome_usuario = %s, sobrenome_usuario = %s,
                    email_usuario = %s, tipo_usuario = %s
                WHERE id_usuario = %s
                """,
                (nome, sobrenome, email, tipo_usuario, id_usuario),
            )
            cursor.execute(
                """
                UPDATE funcionario
                SET email_verificado = %s, id_filial = %s,
                    crf_funcionario = COALESCE(%s, crf_funcionario)
                WHERE id_usuario = %s
                """,
                (email, id_filial, crf, id_usuario),
            )
            if not preserve_director_branch:
                cursor.execute(
                    "DELETE FROM usuario_filial WHERE id_usuario = %s",
                    (id_usuario,),
                )
            if tipo_usuario != "diretor":
                cursor.execute(
                    "INSERT INTO usuario_filial (id_usuario, id_filial) VALUES (%s, %s)",
                    (id_usuario, id_filial),
                )
            connection.commit()
        finally:
            cursor.close()
    except (DuplicateEmployeeData, EmployeeBranchNotFound, EmployeeNotFound, EmployeeEditConflict):
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
