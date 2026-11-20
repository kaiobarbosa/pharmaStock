from flask import Blueprint, jsonify, request

from backend.src.login_and_create_account.use_case.verify_first_use_use_case import (
    verify_first_use
)

blueprint_check_director_exists = Blueprint(
    "blueprint_check_director_exists", __name__
)



@blueprint_check_director_exists.get("/check_director_exists")
def check_director_exists():
    resposta, status_code = verify_first_use()
    return jsonify(resposta), status_code