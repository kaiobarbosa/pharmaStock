import datetime

from model.director_model import *
from infrastructure.repository.director_repository import *
from utils.generate_id import gerar_id_usuario_unico
from infrastructure.external.password_encryption import hash_password


def use_case_create_account_director(nome, sobrenome, cpf, email, senha_simples, codigo_interno):

    if not verify_director_null_fields(nome, sobrenome, cpf, email, senha_simples, codigo_interno):
        return 400
    elif not validate_email(email):
        return 400
    elif not verify_director_cpf_format(cpf):
        return 400
    elif verify_director_email_exists(email):
        return 400
    
    id_usuario = gerar_id_usuario_unico()
    id_funcional = gerar_id_usuario_unico()

    data_criacao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ativo = True

    tipo_usuario = "diretor"

    id_filial = "sede"

    senha_criptografada = hash_password(senha_simples)

    if not create_new_director(id_usuario, nome, sobrenome, email, cpf, tipo_usuario, ativo, data_criacao, id_funcional, senha_criptografada, id_filial, crf="N/A", codigo_interno=codigo_interno):
        return 500
    
    return 200;