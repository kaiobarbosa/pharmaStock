from flask import Blueprint, request, jsonify
from src.login_and_create_account.use_case.create_account_use_case import use_case_create_account_director

blueprint_create_director_account = Blueprint('blueprint_create_director_account', __name__)

@blueprint_create_director_account.route('/create_director_account', methods=['POST'])
def insert_enterprise():
    brute_data = request.get_json()

    response_data, status_code = use_case_create_account_director(
        nome=brute_data.get('nome'),
        sobrenome=brute_data.get('sobrenome'),
        cpf=brute_data.get('cpf'),
        email=brute_data.get('email'),
        senha_simples=brute_data.get('senha_simples'),
        codigo_interno=brute_data.get('codigo_interno')
    )

    return jsonify(response_data), status_code