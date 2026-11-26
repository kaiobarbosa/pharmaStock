from backend.src.products.infrastructure.repository.select_all_products import (
    select_products_from_candidate_query,
)


def _escape_like_prefix(value):
    return value.replace("!", "!!").replace("%", "!%").replace("_", "!_") + "%"


def _build_candidate_query(query, branch_id):
    params = []
    if query:
        prefix = _escape_like_prefix(query)
        product_code_prefix = _escape_like_prefix(query.upper())
        candidate_queries = (
            "SELECT id_produto FROM produto WHERE id_produto LIKE %s ESCAPE '!'",
            "SELECT id_produto FROM produto WHERE nome_produto LIKE %s ESCAPE '!'",
            """
            SELECT mp.id_produto
            FROM medicamento AS m
            INNER JOIN medicamento_produto AS mp
                ON mp.id_medicamento = m.id_medicamento
            WHERE m.principio_ativo LIKE %s ESCAPE '!'
            """,
        )
        candidate_query = "\nUNION\n".join(candidate_queries)
        params.extend((product_code_prefix, prefix, prefix))
    else:
        candidate_query = "SELECT id_produto FROM produto_filial WHERE id_filial = %s"
        params.append(branch_id)

    if query and branch_id:
        candidate_query = f"""
            SELECT DISTINCT matches.id_produto
            FROM (
                {candidate_query}
            ) AS matches
            WHERE EXISTS (
                SELECT 1
                FROM produto_filial AS selected_branch
                WHERE selected_branch.id_filial = %s
                  AND selected_branch.id_produto = matches.id_produto
            )
        """
        params.append(branch_id)
    elif not query and branch_id:
        candidate_query = """
            SELECT DISTINCT id_produto
            FROM produto_filial
            WHERE id_filial = %s
        """
        params = [branch_id]

    return candidate_query, tuple(params)


def select_products_by_filter(query=None, branch_id=None):
    candidate_query, params = _build_candidate_query(query, branch_id)
    return select_products_from_candidate_query(candidate_query, params)
