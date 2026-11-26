from mysql.connector import Error

from backend.configuration.database_connection import conectar_banco


class ProductListingRepositoryError(Exception):
    """Raised when product data cannot be read."""


_PRODUCT_LIST_SELECT = """
    SELECT p.id_produto, p.nome_produto, p.marca, p.descricao, p.preco,
           p.codigo_de_barras, p.quantidade,
           CASE
               WHEN m.id_medicamento IS NOT NULL THEN 'medicine'
               WHEN d.id_dermocosmetico IS NOT NULL THEN 'dermocosmetic'
               WHEN e.id_equipamento IS NOT NULL THEN 'equipment'
               ELSE 'general'
           END AS tipo,
           m.principio_ativo, m.forma_farmaceutica, m.concentracao,
           m.tarja, m.receita, m.tipagem,
           d.tipo_pele, d.volume, d.fator_protecao, d.indicacao,
           e.modelo, e.fabricante, e.especificacoes, e.garantia,
           f.id_filial, f.nome_filial
"""

_PRODUCT_LIST_JOINS = """
    LEFT JOIN medicamento_produto AS mp ON mp.id_produto = p.id_produto
    LEFT JOIN medicamento AS m ON m.id_medicamento = mp.id_medicamento
    LEFT JOIN dermocosmetico_produto AS dp ON dp.id_produto = p.id_produto
    LEFT JOIN dermocosmetico AS d ON d.id_dermocosmetico = dp.id_dermocosmetico
    LEFT JOIN equipamento_produto AS ep ON ep.id_produto = p.id_produto
    LEFT JOIN equipamento AS e ON e.id_equipamento = ep.id_equipamento
    LEFT JOIN produto_filial AS pf ON pf.id_produto = p.id_produto
    LEFT JOIN filial AS f ON f.id_filial = pf.id_filial
"""

_PRODUCT_LIST_ORDER = """
    ORDER BY p.nome_produto ASC, p.id_produto ASC, f.nome_filial ASC
"""


_CATEGORY_FIELDS = {
    "medicine": (
        "principio_ativo",
        "forma_farmaceutica",
        "concentracao",
        "tarja",
        "receita",
        "tipagem",
    ),
    "dermocosmetic": (
        "tipo_pele",
        "volume",
        "fator_protecao",
        "indicacao",
    ),
    "equipment": ("modelo", "fabricante", "especificacoes", "garantia"),
}


def _map_product_rows(rows):
    products = []
    products_by_id = {}
    for row in rows:
        id_produto = row["id_produto"]
        product = products_by_id.get(id_produto)
        if product is None:
            product_type = row["tipo"]
            details = {
                field: row[field]
                for field in _CATEGORY_FIELDS.get(product_type, ())
            }
            if product_type == "medicine" and details["receita"] is not None:
                details["receita"] = bool(details["receita"])

            product = {
                "id_produto": id_produto,
                "nome_produto": row["nome_produto"],
                "marca": row["marca"],
                "descricao": row["descricao"],
                "preco": row["preco"],
                "codigo_de_barras": row["codigo_de_barras"],
                "quantidade": row["quantidade"],
                "tipo": product_type,
                "detalhes": details,
                "filiais": [],
            }
            products_by_id[id_produto] = product
            products.append(product)

        if row["id_filial"] is not None and not any(
            branch["id_filial"] == row["id_filial"] for branch in product["filiais"]
        ):
            product["filiais"].append(
                {
                    "id_filial": row["id_filial"],
                    "nome_filial": row["nome_filial"],
                }
            )

    return products


def _select_products(query, params=()):
    connection = conectar_banco()

    try:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
        finally:
            cursor.close()
    except Error as error:
        raise ProductListingRepositoryError from error
    finally:
        connection.close()

    return _map_product_rows(rows)


def select_all_products():
    query = (
        _PRODUCT_LIST_SELECT
        + " FROM produto AS p\n"
        + _PRODUCT_LIST_JOINS
        + _PRODUCT_LIST_ORDER
    )
    return _select_products(query)


def select_products_from_candidate_query(candidate_query, params):
    """Load matching products using a repository-owned candidate-ID query."""
    query = (
        _PRODUCT_LIST_SELECT
        + " FROM produto AS p\n"
        + " INNER JOIN (\n"
        + candidate_query
        + "\n ) AS product_matches ON product_matches.id_produto = p.id_produto\n"
        + _PRODUCT_LIST_JOINS
        + _PRODUCT_LIST_ORDER
    )
    return _select_products(query, params)
