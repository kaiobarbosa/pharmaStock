from configuration.database_connection import conectar_banco


def verify_director_exists(codigo_interno):
    sql = "select id_funcionario from funcionario where codigo_interno = %s;"

    connection = conectar_banco()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(sql, (codigo_interno,))
        diretor = cursor.fetchone()
        return diretor is not None
    finally:
        cursor.close()
        connection.close()


def verify_director_email_exists(email):
    sql = "select * from usuario where email_usuario = %s;"

    connection = conectar_banco()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(sql, (email,))
        funcionarios_retornados = cursor.fetchall()
        return funcionarios_retornados
    finally:
        cursor.close()
        connection.close()


def create_new_director(id_user, nome, sobrenome, email, cpf, tipo_usuario, ativo, criado_em, id_funcional, password, id_filial,  crf, codigo_interno):
    sql = "insert into usuario (id_usuario, nome_usuario, sobrenome_usuario, email_usuario, cpf_usuario, tipo_usuario, ativo, criado_em) values (%s, %s, %s, %s, %s, %s, %s, %s);"

    connection = conectar_banco()
    cursor = connection.cursor()

    try:
        cursor.execute(sql,(id_user, nome, sobrenome, email, cpf, tipo_usuario, ativo, criado_em), )

        if cursor.rowcount == 1:
            status_funcional = create_director_functional(id_funcional=id_funcional, password=password, email=email, id_filial=id_filial, crf=crf or "N/A", codigo_interno=codigo_interno, id_usuario=id_user, connection=connection,)

            if status_funcional == 200:
                connection.commit()
                return 200

        connection.rollback()
        return 500

    except Exception as erro:
        connection.rollback()
        print(f"Erro ao criar conta de diretor: {erro}")
        return 500

    finally:
        cursor.close()
        connection.close()


def create_director_functional(id_funcional, password, email, id_filial, crf, codigo_interno, id_usuario, connection=None,):
    
    sql = "insert into funcionario (id_funcionario, senha_funcionario, email_verificado, id_filial, crf_funcionario, codigo_interno, id_usuario) values (%s, %s, %s, %s, %s, %s, %s);"

    conexao_propria = connection is None
    if conexao_propria:
        connection = conectar_banco()

    cursor = connection.cursor()

    try:
        cursor.execute(sql,(id_funcional,password,email,id_filial,crf or "N/A",codigo_interno, id_usuario,),)

        if cursor.rowcount == 1:
            if conexao_propria:
                connection.commit()
            return 200

        if conexao_propria:
            connection.rollback()
        return 500

    except Exception as erro:
        if conexao_propria:
            connection.rollback()
            return 500
        raise erro

    finally:
        cursor.close()
        if conexao_propria:
            connection.close()
