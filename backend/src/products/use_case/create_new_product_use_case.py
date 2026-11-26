from backend.configuration.database_connection import DatabaseUnavailable
from backend.src.employees.infrastructure.repository.employee_repository import (
    EmployeeRepositoryError,
    get_user_role_by_email,
)
from backend.src.employees.model.employee_model import normalize_employee_role
from backend.src.products.infrastructure.repository.create_new_product import (
    DuplicateProductData,
    ProductBranchNotFound,
    ProductRepositoryError,
    create_new_product,
)
from backend.src.products.model.products_model import validate_new_product_data
from backend.src.utils.generate_id import gerar_codigo_aleatorio


def create_new_product_use_case(data, actor_email):
    normalized, errors = validate_new_product_data(data)
    if errors:
        return {
            "ok": False,
            "message": "Confira os dados informados.",
            "errors": errors,
        }, 400

    try:
        actor = get_user_role_by_email(actor_email)
    except DatabaseUnavailable:
        return {
            "ok": False,
            "message": "Banco de dados indisponível. Tente novamente mais tarde.",
        }, 503
    except EmployeeRepositoryError:
        return {
            "ok": False,
            "message": "Não foi possível validar as permissões do usuário.",
        }, 500

    actor_role = normalize_employee_role(actor["role"]) if actor else None
    if (
        not actor
        or not actor["active"]
        or actor_role not in ("diretor", "gerente", "farmaceutico")
    ):
        return {
            "ok": False,
            "message": "Sua conta não tem permissão para cadastrar produtos.",
        }, 403

    id_produto = gerar_codigo_aleatorio()
    id_categoria = None
    if normalized["type"] != "general":
        id_categoria = gerar_codigo_aleatorio()
        while id_categoria == id_produto:
            id_categoria = gerar_codigo_aleatorio()

    try:
        create_new_product(
            id_produto=id_produto,
            id_categoria=id_categoria,
            data=normalized,
        )
    except DuplicateProductData:
        return {
            "ok": False,
            "message": "Um identificador gerado já está em uso. Tente novamente.",
        }, 409
    except ProductBranchNotFound:
        return {"ok": False, "message": "A filial selecionada não foi encontrada."}, 404
    except DatabaseUnavailable:
        return {
            "ok": False,
            "message": "Banco de dados indisponível. Tente novamente mais tarde.",
        }, 503
    except ProductRepositoryError:
        return {
            "ok": False,
            "message": "Não foi possível concluir o cadastro. Tente novamente.",
        }, 500

    return {
        "ok": True,
        "message": "Produto cadastrado com sucesso.",
        "product": {
            "id_produto": id_produto,
            "id_categoria": id_categoria,
            "tipo": normalized["type"],
            "nome": normalized["name"],
            "marca": normalized["brand"],
            "codigo_de_barras": normalized["barcode"],
            "quantidade": normalized["quantity"],
            "id_filial": normalized["branch_id"],
        },
    }, 201
