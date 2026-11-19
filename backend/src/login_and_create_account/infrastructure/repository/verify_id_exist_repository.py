from configuration.database_connection import conectar_banco


def verify_id_exist(codigo_interno):
    sql = "select * from usuario where codigo_interno = %s;"

    connection = conectar_banco()
    cursor = connection.cursor(dictionary=True) 


    cursor.execute(sql, (codigo_interno,))
    funcionarios_retornados = cursor.fetchall()
    connection.commit()

    cursor.close()
    connection.close()

    return funcionarios_retornados