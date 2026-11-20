from backend.configuration.database_connection import conectar_banco


def verify_id_exist(id_usuario):
    connection = conectar_banco()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM usuario WHERE id_usuario = %s LIMIT 1", (id_usuario,)
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()
    finally:
        connection.close()
