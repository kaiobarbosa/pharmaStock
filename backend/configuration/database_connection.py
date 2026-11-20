import os

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error


class DatabaseUnavailable(Exception):
    """Raised when the application cannot establish a MySQL connection."""


def conectar_banco():
    load_dotenv()

    config = {
        "host": os.getenv("DB_HOST"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME"),
        "connection_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "5")),
    }
    missing = [key for key in ("host", "user", "database") if not config[key]]
    if config["password"] is None:
        missing.append("password")
    if missing:
        raise DatabaseUnavailable("Configuração do banco incompleta.")

    try:
        return mysql.connector.connect(**config)
    except Error as error:
        raise DatabaseUnavailable("Não foi possível conectar ao banco de dados.") from error
