from flask import Blueprint, jsonify, request

from backend.src.branchs.use_case.edit_branch_data_use_case import (
    edit_branch_data_use_case,
)

blueprint_edit_branch = Blueprint("blueprint_edit_branch", __name__)


@blueprint_edit_branch.put("/api/branches/<id_filial>")
def edit_branch(id_filial):
    if not request.is_json:
        return jsonify({"ok": False, "message": "O corpo deve estar em formato JSON."}), 415

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"ok": False, "message": "O corpo JSON enviado é inválido."}), 400

    response_data, status_code = edit_branch_data_use_case(
        id_filial=id_filial,
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
