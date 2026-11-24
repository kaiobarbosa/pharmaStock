from backend.configuration.database_connection import DatabaseUnavailable
from backend.src.branchs.infrastructure.repository.edit_branch_repository import (
    BranchEditRepositoryError,
    DuplicateBranchEditData,
    update_branch_data,
)
from backend.src.branchs.model.new_branch_model import normalize_branch_data


def _branch_response(id_filial, id_endereco, data):
    return {
        "id_filial": id_filial,
        "id_endereco": id_endereco,
        "nome_filial": data["nome"],
        "cep": data["cep"],
        "logradouro": data["logradouro"],
        "numero": data["numero"],
        "complemento": data["complemento"],
        "bairro": data["bairro"],
        "cidade": data["cidade"],
        "estado": data["estado"],
    }


def edit_branch_data_use_case(
    id_filial,
    nome,
    cep,
    logradouro,
    numero,
    complemento,
    bairro,
    cidade,
    estado,
):
    if not isinstance(id_filial, str) or len(id_filial.strip()) != 6:
        return {"ok": False, "message": "Identificador de filial inválido."}, 400

    id_filial = id_filial.strip()
    normalized, errors = normalize_branch_data(
        nome=nome,
        cep=cep,
        logradouro=logradouro,
        numero=numero,
        complemento=complemento,
        bairro=bairro,
        cidade=cidade,
        estado=estado,
    )
    if errors:
        return {
            "ok": False,
            "message": "Confira os dados informados.",
            "errors": errors,
        }, 400

    try:
        result = update_branch_data(
            id_filial=id_filial,
            nome_filial=normalized["nome"],
            cep=normalized["cep"],
            logradouro=normalized["logradouro"],
            numero=normalized["numero"],
            complemento=normalized["complemento"],
            bairro=normalized["bairro"],
            cidade=normalized["cidade"],
            estado=normalized["estado"],
        )
    except DuplicateBranchEditData:
        return {
            "ok": False,
            "message": "Um identificador do endereço já está em uso. Tente novamente.",
        }, 409
    except DatabaseUnavailable:
        return {
            "ok": False,
            "message": "Banco de dados indisponível. Tente novamente mais tarde.",
        }, 503
    except BranchEditRepositoryError:
        return {
            "ok": False,
            "message": "Não foi possível atualizar a filial. Tente novamente.",
        }, 500

    if result is None:
        return {"ok": False, "message": "Filial não encontrada."}, 404

    return {
        "ok": True,
        "message": "Filial atualizada com sucesso.",
        "branch": _branch_response(id_filial, result["id_endereco"], normalized),
    }, 200
