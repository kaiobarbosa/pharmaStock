from configuration.database_connection import conectar_banco

def verify_director_exists(codigo_interno):
    # Aqui você pode implementar a lógica para verificar se o diretor existe no banco de dados
    # Por exemplo, você pode fazer uma consulta SQL para verificar se o código interno está presente na tabela de diretores
    # Retorne True se o diretor existir, caso contrário, retorne False
    return True  # Substitua isso pela lógica real de verificação

def verify_director_email_exists(email):
    sql = "select * from usuario where email = %s;"

    connection = conectar_banco()
    cursor = connection.cursor(dictionary=True) 


    cursor.execute(sql, (email,))
    funcionarios_retornados = cursor.fetchall()
    connection.commit()

    cursor.close()
    connection.close()

    return funcionarios_retornados