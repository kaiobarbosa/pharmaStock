from flask import Blueprint, jsonify, request

from backend.src.branchs.use_case.new_branch_use_case import (
    create_branch as use_case_create_branch,
    list_branches as use_case_list_branches,
)

blueprint_create_branch = Blueprint("blueprint_create_branch", __name__)


def _request_json():
    if not request.is_json:
        return None, (
            jsonify({"ok": False, "message": "O corpo deve estar em formato JSON."}),
            415,
        )

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, (
            jsonify({"ok": False, "message": "O corpo JSON enviado é inválido."}),
            400,
        )
    return data, None


@blueprint_create_branch.post("/api/create_branch")
@blueprint_create_branch.post("/create_branch")
def create_branch():
    data, error_response = _request_json()
    if error_response:
        return error_response

    response_data, status_code = use_case_create_branch(
        nome=data.get("nome"),
        cep=data.get("cep"),
        logradouro=data.get("logradouro"),
        numero=data.get("numero"),
        complemento=data.get("complemento"),
        bairro=data.get("bairro"),
        cidade=data.get("cidade"),
        estado=data.get("estado"),
    )
    return jsonify(response_data), status_code


@blueprint_create_branch.get("/api/branches")
def list_branches():
    response_data, status_code = use_case_list_branches()
    return jsonify(response_data), status_code
