from backend.configuration.database_connection import DatabaseUnavailable
from backend.src.branchs.infrastructure.repository.new_branch_repository import (
    BranchRepositoryError,
    DuplicateBranchData,
    create_new_branch,
    get_all_branches,
)
from backend.src.branchs.model.new_branch_model import normalize_branch_data
from backend.src.utils.generate_id import gerar_id_usuario_unico


def _branch_data(nome, cep, logradouro, numero, complemento, bairro, cidade, estado):
    return normalize_branch_data(
        nome=nome,
        cep=cep,
        logradouro=logradouro,
        numero=numero,
        complemento=complemento,
        bairro=bairro,
        cidade=cidade,
        estado=estado,
    )


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


def create_branch(nome, cep, logradouro, numero, complemento, bairro, cidade, estado):
    normalized, errors = _branch_data(
        nome, cep, logradouro, numero, complemento, bairro, cidade, estado
    )
    if errors:
        return {
            "ok": False,
            "message": "Confira os dados informados.",
            "errors": errors,
        }, 400

    id_filial = gerar_id_usuario_unico()
    id_endereco = gerar_id_usuario_unico()
    while id_endereco == id_filial:
        id_endereco = gerar_id_usuario_unico()

    try:
        create_new_branch(
            id_filial=id_filial,
            nome_filial=normalized["nome"],
            id_endereco=id_endereco,
            cep=normalized["cep"],
            logradouro=normalized["logradouro"],
            numero=normalized["numero"],
            complemento=normalized["complemento"],
            bairro=normalized["bairro"],
            cidade=normalized["cidade"],
            estado=normalized["estado"],
        )
    except DuplicateBranchData:
        return {
            "ok": False,
            "message": "Um identificador gerado já está em uso. Tente novamente.",
        }, 409
    except DatabaseUnavailable:
        return {
            "ok": False,
            "message": "Banco de dados indisponível. Tente novamente mais tarde.",
        }, 503
    except BranchRepositoryError:
        return {
            "ok": False,
            "message": "Não foi possível cadastrar a filial. Tente novamente.",
        }, 500

    return {
        "ok": True,
        "message": "Filial cadastrada com sucesso.",
        "branch": _branch_response(id_filial, id_endereco, normalized),
    }, 201


def list_branches():
    try:
        branches = get_all_branches()
    except DatabaseUnavailable:
        return {
            "ok": False,
            "message": "Banco de dados indisponível. Tente novamente mais tarde.",
        }, 503
    except BranchRepositoryError:
        return {
            "ok": False,
            "message": "Não foi possível carregar as filiais. Tente novamente.",
        }, 500

    return {"ok": True, "branches": branches}, 200
