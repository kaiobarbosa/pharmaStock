from mysql.connector import Error, IntegrityError

from backend.configuration.database_connection import conectar_banco


class DuplicateProductData(Exception):
    """Raised when one of the generated product identifiers is already in use."""


class ProductBranchNotFound(Exception):
    """Raised when the selected branch does not exist."""


class ProductRepositoryError(Exception):
    """Raised when product data cannot be stored."""


def create_new_product(id_produto, id_categoria, data):
    connection = conectar_banco()

    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "SELECT id_filial FROM filial WHERE id_filial = %s LIMIT 1",
                (data["branch_id"],),
            )
            branch_row = cursor.fetchone()
            if branch_row is None:
                raise ProductBranchNotFound

            cursor.execute(
                """
                INSERT INTO produto
                    (id_produto, nome_produto, marca, descricao, preco,
                     codigo_de_barras, quantidade)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    id_produto,
                    data["name"],
                    data["brand"],
                    data["description"],
                    data["price"],
                    data["barcode"],
                    data["quantity"],
                ),
            )

            product_type = data["type"]
            if product_type == "medicine":
                cursor.execute(
                    """
                    INSERT INTO medicamento
                        (id_medicamento, principio_ativo, forma_farmaceutica,
                         concentracao, tarja, receita, tipagem)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        id_categoria,
                        data["activeIngredient"],
                        data["pharmaceuticalForm"],
                        data["concentration"],
                        data["prescriptionBand"],
                        data["prescriptionRequired"],
                        data["classification"],
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO medicamento_produto (id_produto, id_medicamento)
                    VALUES (%s, %s)
                    """,
                    (id_produto, id_categoria),
                )
            elif product_type == "dermocosmetic":
                cursor.execute(
                    """
                    INSERT INTO dermocosmetico
                        (id_dermocosmetico, tipo_pele, volume, fator_protecao, indicacao)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        id_categoria,
                        data["skinType"],
                        data["volume"],
                        data["sunProtectionFactor"],
                        data["indication"],
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO dermocosmetico_produto (id_produto, id_dermocosmetico)
                    VALUES (%s, %s)
                    """,
                    (id_produto, id_categoria),
                )
            elif product_type == "equipment":
                cursor.execute(
                    """
                    INSERT INTO equipamento
                        (id_equipamento, modelo, fabricante, especificacoes, garantia)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        id_categoria,
                        data["model"],
                        data["manufacturer"],
                        data["specifications"],
                        data["warranty"],
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO equipamento_produto (id_produto, id_equipamento)
                    VALUES (%s, %s)
                    """,
                    (id_produto, id_categoria),
                )

            cursor.execute(
                "INSERT INTO produto_filial (id_produto, id_filial) VALUES (%s, %s)",
                (id_produto, branch_row[0]),
            )
            connection.commit()
        finally:
            cursor.close()
    except ProductBranchNotFound:
        connection.rollback()
        raise
    except IntegrityError as error:
        connection.rollback()
        if error.errno == 1062:
            raise DuplicateProductData from error
        raise ProductRepositoryError from error
    except Error as error:
        connection.rollback()
        raise ProductRepositoryError from error
    finally:
        connection.close()

    return True
