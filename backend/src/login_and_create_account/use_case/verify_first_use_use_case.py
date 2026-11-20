from infrastructure.repository.verify_id_exist_repository import verify_director_exist

def verify_first_use() -> tuple[dict, int]:

    try:
        existe_diretor = verify_director_exist()
        return {
            "director_exists": existe_diretor,
            "requires_initial_setup": not existe_diretor,
        }, 200

    except ConnectionError as erro:
        return {"erro": str(erro)}, 503
    except Exception as erro:
        return {"erro": f"Falha ao verificar existência de diretor: {erro}"}, 500
