from model.director_model import *
from infrastructure.repository.director_repository import *
from utils.generate_id import gerar_id_usuario_unico

def use_case_create_account(nome, sobrenome, cpf, email, senha, codigo_interno):

    if not verify_director_null_fields(nome, sobrenome, cpf, email, senha, codigo_interno):
        return 400
    elif not validate_email(email):
        return 400
    elif not verify_director_cpf_format(cpf):
        return 400
    elif verify_director_email_exists(email):
        return 400
    
    codigo_interno = gerar_id_usuario_unico()

    

    return 200;