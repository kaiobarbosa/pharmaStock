import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

def conectar_banco():
    try:

        load_dotenv()
       
        conexao = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )

        if conexao.is_connected():
            db_info = conexao.get_server_info()
            print(f"Conectado ao servidor MySQL versão: {db_info}")

            cursor = conexao.cursor()
            cursor.execute("SELECT DATABASE();")
            linha = cursor.fetchone()
            print(f"Você está conectado ao banco: {linha[0]}")

    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
        conexao = None

    return conexao