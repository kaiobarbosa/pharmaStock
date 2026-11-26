import unittest
from unittest.mock import patch

from flask import Flask

from backend.src.login_and_create_account.use_case.token_use_case import (
    create_user_token,
)
from backend.src.products.infrastructure.repository import (
    create_new_product as create_product_repository,
)
from backend.src.products.infrastructure.repository import (
    select_all_products as select_products_repository,
)
from backend.src.products.model.products_model import validate_new_product_data
from backend.src.products.presentation.create_new_product_presentation import (
    blueprint_create_product,
)
from backend.src.products.presentation.select_all_products_presentation import (
    blueprint_select_all_products,
)
from backend.src.products.presentation.select_products_by_filter_presentation import (
    blueprint_select_products_by_filter,
)
from backend.src.products.use_case import create_new_product_use_case as create_product_use_case
from backend.src.products.use_case import select_all_products_use_case as select_products_use_case
from backend.src.products.infrastructure.repository.select_products_by_filter_repository import (
    _build_candidate_query,
)
from backend.src.products.model.products_model import validate_product_search_filters
from backend.src.products.use_case import select_products_by_filter_use_case as filter_products_use_case


def valid_product_data(product_type="general"):
    data = {
        "type": product_type,
        "name": "Produto teste",
        "brand": "Marca teste",
        "description": "Descrição de teste",
        "price": "19.90",
        "barcode": "7891234567890",
        "quantity": "12",
        "branch": "FIL001",
    }
    if product_type == "medicine":
        data.update(
            {
                "activeIngredient": "Dipirona",
                "pharmaceuticalForm": "Comprimido",
                "concentration": "500mg",
                "prescriptionBand": "Sem tarja",
                "prescriptionRequired": "Não",
                "classification": "Comum",
            }
        )
    elif product_type == "dermocosmetic":
        data.update(
            {
                "skinType": "Pele mista",
                "volume": "50ml",
                "sunProtectionFactor": "FPS 30",
                "indication": "Hidratação",
            }
        )
    elif product_type == "equipment":
        data.update(
            {
                "model": "HEM-7122",
                "manufacturer": "Fabricante teste",
                "specifications": "Especificação de teste",
                "warranty": "1 ano",
            }
        )
    return data


class FakeCursor:
    def __init__(self, rows=None, branch_row=("FIL001",)):
        self.rows = rows or []
        self.branch_row = branch_row
        self.executed = []
        self.closed = False

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return self.branch_row

    def fetchall(self):
        return self.rows

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, cursor):
        self.fake_cursor = cursor
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self, **kwargs):
        return self.fake_cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


class ProductModelTests(unittest.TestCase):
    def test_validates_and_normalizes_each_supported_product_type(self):
        for product_type in ("general", "medicine", "dermocosmetic", "equipment"):
            with self.subTest(product_type=product_type):
                normalized, errors = validate_new_product_data(valid_product_data(product_type))
                self.assertEqual(errors, {})
                self.assertEqual(normalized["type"], product_type)
                self.assertEqual(normalized["price"], "19.90")
                self.assertEqual(normalized["branch_id"], "FIL001")

        medicine, errors = validate_new_product_data(valid_product_data("medicine"))
        self.assertEqual(errors, {})
        self.assertIs(medicine["prescriptionRequired"], False)

    def test_rejects_invalid_type_lengths_numbers_and_branch_ids(self):
        data = valid_product_data("equipment")
        data.update(
            {
                "type": "equipment; DROP TABLE produto",
                "name": "x" * 101,
                "price": "-1.239",
                "quantity": "-2",
                "branch": "FIL001; DROP",
                "specifications": "x" * 101,
            }
        )

        normalized, errors = validate_new_product_data(data)

        for field in ("type", "name", "price", "quantity", "branch"):
            self.assertIn(field, errors)

        data["type"] = "equipment"
        _, equipment_errors = validate_new_product_data(data)
        self.assertIn("specifications", equipment_errors)

    def test_requires_category_fields(self):
        data = valid_product_data("medicine")
        del data["activeIngredient"]
        _, errors = validate_new_product_data(data)
        self.assertIn("activeIngredient", errors)

    def test_search_filter_validation_bounds_query_and_branch(self):
        normalized, errors = validate_product_search_filters(
            query="  Dipirona  ", branch_id="fil001", require_filter=True
        )
        self.assertEqual(errors, {})
        self.assertEqual(normalized, {"query": "Dipirona", "branch_id": "FIL001"})

        _, errors = validate_product_search_filters(
            query="x" * 101, branch_id="FIL001", require_filter=True
        )
        self.assertIn("query", errors)

        _, errors = validate_product_search_filters(
            query=None, branch_id="FIL001; DROP TABLE filial", require_filter=True
        )
        self.assertIn("branch_id", errors)


class ProductUseCaseTests(unittest.TestCase):
    @patch("backend.src.products.use_case.create_new_product_use_case.create_new_product")
    @patch("backend.src.products.use_case.create_new_product_use_case.get_user_role_by_email")
    def test_customer_cannot_create_product(self, get_actor, create_product):
        get_actor.return_value = {"role": "cliente", "active": True}

        result, status = create_product_use_case.create_new_product_use_case(
            valid_product_data(), "customer@example.com"
        )

        self.assertEqual(status, 403)
        self.assertFalse(result["ok"])
        create_product.assert_not_called()

    @patch("backend.src.products.use_case.create_new_product_use_case.create_new_product")
    @patch("backend.src.products.use_case.create_new_product_use_case.get_user_role_by_email")
    def test_attendant_cannot_create_product(self, get_actor, create_product):
        get_actor.return_value = {"role": "atendente", "active": True}

        result, status = create_product_use_case.create_new_product_use_case(
            valid_product_data(), "attendant@example.com"
        )

        self.assertEqual(status, 403)
        self.assertFalse(result["ok"])
        create_product.assert_not_called()

    @patch("backend.src.products.use_case.create_new_product_use_case.gerar_codigo_aleatorio")
    @patch("backend.src.products.use_case.create_new_product_use_case.create_new_product")
    @patch("backend.src.products.use_case.create_new_product_use_case.get_user_role_by_email")
    def test_pharmacist_can_create_product(self, get_actor, create_product, generate_id):
        get_actor.return_value = {"role": "farmaceutico", "active": True}
        generate_id.return_value = "PRD001"

        result, status = create_product_use_case.create_new_product_use_case(
            valid_product_data(), "pharmacist@example.com"
        )

        self.assertEqual(status, 201)
        self.assertTrue(result["ok"])
        create_product.assert_called_once()

    @patch("backend.src.products.use_case.create_new_product_use_case.get_user_role_by_email")
    def test_invalid_data_is_rejected_before_database_authorization_lookup(self, get_actor):
        data = valid_product_data()
        data["price"] = "1; DROP TABLE produto"

        result, status = create_product_use_case.create_new_product_use_case(
            data, "employee@example.com"
        )

        self.assertEqual(status, 400)
        self.assertIn("price", result["errors"])
        get_actor.assert_not_called()

    @patch("backend.src.products.use_case.select_all_products_use_case.select_all_products")
    @patch("backend.src.products.use_case.select_all_products_use_case.get_user_role_by_email")
    def test_product_listing_is_restricted_to_active_employee_accounts(
        self, get_actor, select_products
    ):
        get_actor.return_value = {"role": "cliente", "active": True}

        result, status = select_products_use_case.select_all_products_use_case(
            "customer@example.com"
        )

        self.assertEqual(status, 403)
        self.assertFalse(result["ok"])
        select_products.assert_not_called()

    @patch("backend.src.products.use_case.select_products_by_filter_use_case.select_products_by_filter")
    @patch("backend.src.products.use_case.select_products_by_filter_use_case.get_user_role_by_email")
    def test_filter_use_case_combines_text_and_branch(self, get_actor, select_products):
        get_actor.return_value = {"role": "gerente", "active": True}
        select_products.return_value = [{"id_produto": "PRD001"}]

        result, status = filter_products_use_case.select_products_by_filter_use_case(
            query="Dipirona", branch_id="fil001", actor_email="manager@example.com"
        )

        self.assertEqual(status, 200)
        self.assertEqual(result["products"], [{"id_produto": "PRD001"}])
        select_products.assert_called_once_with(query="Dipirona", branch_id="FIL001")

    @patch("backend.src.products.use_case.select_products_by_filter_use_case.select_products_by_filter")
    @patch("backend.src.products.use_case.select_products_by_filter_use_case.get_user_role_by_email")
    def test_filter_use_case_rejects_empty_filter_without_database_work(
        self, get_actor, select_products
    ):
        result, status = filter_products_use_case.select_products_by_filter_use_case(
            query="", branch_id="all", actor_email="employee@example.com"
        )

        self.assertEqual(status, 400)
        self.assertFalse(result["ok"])
        get_actor.assert_not_called()
        select_products.assert_not_called()

    @patch("backend.src.products.use_case.select_all_products_use_case.select_all_products")
    @patch("backend.src.products.use_case.select_all_products_use_case.get_user_role_by_email")
    def test_inactive_employee_cannot_list_products(self, get_actor, select_products):
        get_actor.return_value = {"role": "gerente", "active": False}

        result, status = select_products_use_case.select_all_products_use_case(
            "manager@example.com"
        )

        self.assertEqual(status, 403)
        self.assertFalse(result["ok"])
        select_products.assert_not_called()


class ProductRepositoryTests(unittest.TestCase):
    def test_filter_queries_are_parameterized_and_use_prefix_patterns(self):
        malicious_query = "X%'_! OR 1=1 --"
        candidate_query, params = _build_candidate_query(malicious_query, "FIL001")

        self.assertNotIn(malicious_query, candidate_query)
        self.assertIn("UNION", candidate_query)
        self.assertIn("m.principio_ativo LIKE %s ESCAPE '!'", candidate_query)
        self.assertIn("selected_branch.id_filial = %s", candidate_query)
        self.assertEqual(len(params), 4)
        expected_prefix = (
            malicious_query.replace("!", "!!").replace("%", "!%").replace("_", "!_")
            + "%"
        )
        self.assertEqual(params[1], expected_prefix)
        self.assertEqual(params[2], expected_prefix)
        for pattern in params[:3]:
            self.assertTrue(pattern.endswith("%"))
            self.assertFalse(pattern.startswith("%"))
        self.assertEqual(params[-1], "FIL001")

    def test_branch_only_filter_uses_the_branch_leading_index_shape(self):
        candidate_query, params = _build_candidate_query(None, "FIL002")

        self.assertIn("SELECT DISTINCT id_produto", candidate_query)
        self.assertIn("FROM produto_filial", candidate_query)
        self.assertIn("WHERE id_filial = %s", candidate_query)
        self.assertEqual(params, ("FIL002",))

    def test_create_uses_parameters_and_commits_all_category_associations(self):
        for product_type, expected_table in (
            ("general", None),
            ("medicine", "medicamento_produto"),
            ("dermocosmetic", "dermocosmetico_produto"),
            ("equipment", "equipamento_produto"),
        ):
            with self.subTest(product_type=product_type):
                cursor = FakeCursor()
                connection = FakeConnection(cursor)
                data = valid_product_data(product_type)
                data["name"] = "Produto'); DROP TABLE produto;--"
                normalized, errors = validate_new_product_data(data)
                self.assertEqual(errors, {})

                with patch.object(
                    create_product_repository, "conectar_banco", return_value=connection
                ):
                    create_product_repository.create_new_product("PRD001", "CAT001", normalized)

                queries = [query for query, _ in cursor.executed]
                params = [params for _, params in cursor.executed if params]
                self.assertTrue(any("INSERT INTO produto" in query for query in queries))
                self.assertTrue(any("INSERT INTO produto_filial" in query for query in queries))
                if expected_table:
                    self.assertTrue(any(expected_table in query for query in queries))
                self.assertFalse(any("DROP TABLE" in query for query in queries))
                self.assertTrue(
                    any("Produto'); DROP TABLE produto;--" in values for values in params)
                )
                self.assertTrue(connection.committed)
                self.assertFalse(connection.rolled_back)
                self.assertTrue(connection.closed)

    def test_missing_branch_rolls_back_without_inserting_product(self):
        cursor = FakeCursor(branch_row=None)
        connection = FakeConnection(cursor)
        normalized, errors = validate_new_product_data(valid_product_data())
        self.assertEqual(errors, {})

        with patch.object(create_product_repository, "conectar_banco", return_value=connection):
            with self.assertRaises(create_product_repository.ProductBranchNotFound):
                create_product_repository.create_new_product("PRD001", None, normalized)

        self.assertEqual(len(cursor.executed), 1)
        self.assertTrue(connection.rolled_back)
        self.assertFalse(connection.committed)

    def test_listing_merges_category_details_and_multiple_branches(self):
        common = {
            "id_produto": "PRD001",
            "nome_produto": "Dipirona",
            "marca": "Marca",
            "descricao": "Descrição",
            "preco": "19.90",
            "codigo_de_barras": "7891234567890",
            "quantidade": "12",
            "tipo": "medicine",
            "principio_ativo": "Dipirona",
            "forma_farmaceutica": "Comprimido",
            "concentracao": "500mg",
            "tarja": "Sem Tarja",
            "receita": 0,
            "tipagem": "Comum",
            "tipo_pele": None,
            "volume": None,
            "fator_protecao": None,
            "indicacao": None,
            "modelo": None,
            "fabricante": None,
            "especificacoes": None,
            "garantia": None,
        }
        rows = [
            {**common, "id_filial": "FIL001", "nome_filial": "Filial Centro"},
            {**common, "id_filial": "FIL001", "nome_filial": "Filial Centro"},
            {**common, "id_filial": "FIL002", "nome_filial": "Filial Norte"},
        ]
        dermocosmetic = {
            **common,
            "id_produto": "PRD002",
            "nome_produto": "Protetor solar",
            "tipo": "dermocosmetic",
            "principio_ativo": None,
            "forma_farmaceutica": None,
            "concentracao": None,
            "tarja": None,
            "receita": None,
            "tipagem": None,
            "tipo_pele": "Pele oleosa",
            "volume": "50g",
            "fator_protecao": "FPS 60",
            "indicacao": "Proteção solar",
            "id_filial": None,
            "nome_filial": None,
        }
        equipment = {
            **common,
            "id_produto": "PRD003",
            "nome_produto": "Termômetro",
            "tipo": "equipment",
            "principio_ativo": None,
            "forma_farmaceutica": None,
            "concentracao": None,
            "tarja": None,
            "receita": None,
            "tipagem": None,
            "tipo_pele": None,
            "volume": None,
            "fator_protecao": None,
            "indicacao": None,
            "modelo": "TH1027",
            "fabricante": "G-Tech",
            "especificacoes": "Visor LCD",
            "garantia": "1 ano",
            "id_filial": None,
            "nome_filial": None,
        }
        general = {
            **common,
            "id_produto": "PRD004",
            "nome_produto": "Algodão",
            "tipo": "general",
            "principio_ativo": None,
            "forma_farmaceutica": None,
            "concentracao": None,
            "tarja": None,
            "receita": None,
            "tipagem": None,
            "tipo_pele": None,
            "volume": None,
            "fator_protecao": None,
            "indicacao": None,
            "modelo": None,
            "fabricante": None,
            "especificacoes": None,
            "garantia": None,
            "id_filial": None,
            "nome_filial": None,
        }
        rows.extend((dermocosmetic, equipment, general))
        cursor = FakeCursor(rows=rows)
        connection = FakeConnection(cursor)

        with patch.object(
            select_products_repository, "conectar_banco", return_value=connection
        ):
            products = select_products_repository.select_all_products()

        self.assertEqual(len(products), 4)
        self.assertEqual(products[0]["tipo"], "medicine")
        self.assertIs(products[0]["detalhes"]["receita"], False)
        self.assertEqual(
            products[0]["filiais"],
            [
                {"id_filial": "FIL001", "nome_filial": "Filial Centro"},
                {"id_filial": "FIL002", "nome_filial": "Filial Norte"},
            ],
        )
        self.assertEqual(products[1]["detalhes"]["fator_protecao"], "FPS 60")
        self.assertEqual(products[2]["detalhes"]["modelo"], "TH1027")
        self.assertEqual(products[3]["detalhes"], {})


class ProductPresentationTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["JWT_SECRET_KEY"] = "test-secret-key-that-is-long-enough"
        self.app.register_blueprint(blueprint_create_product)
        self.app.register_blueprint(blueprint_select_all_products)
        self.app.register_blueprint(blueprint_select_products_by_filter)
        self.client = self.app.test_client()
        self.token = create_user_token("Funcionário Teste", "employee@example.com", self.app.config["JWT_SECRET_KEY"])

    def test_both_product_endpoints_reject_missing_and_invalid_tokens(self):
        for method, path, kwargs in (
            (self.client.post, "/api/products", {"json": valid_product_data()}),
            (self.client.get, "/api/products", {}),
        ):
            with self.subTest(path=path, token="missing"):
                response = method(path, **kwargs)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.headers.get("Cache-Control"), "no-store")

            invalid_kwargs = {**kwargs, "headers": {"Authorization": "Bearer invalid.token"}}
            with self.subTest(path=path, token="invalid"):
                response = method(path, **invalid_kwargs)
                self.assertEqual(response.status_code, 401)

    @patch("backend.src.products.presentation.create_new_product_presentation.create_new_product_use_case")
    def test_create_endpoint_requires_json_and_passes_authenticated_email(self, use_case):
        use_case.return_value = ({"ok": True, "product": {"id_produto": "PRD001"}}, 201)

        non_json = self.client.post("/api/products", data="payload", content_type="text/plain")
        self.assertEqual(non_json.status_code, 415)

        response = self.client.post(
            "/api/products",
            json=valid_product_data(),
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.assertEqual(response.status_code, 201)
        use_case.assert_called_once_with(valid_product_data(), "employee@example.com")

    @patch("backend.src.products.presentation.select_all_products_presentation.select_all_products_use_case")
    def test_listing_endpoint_returns_no_store_catalog_response(self, use_case):
        use_case.return_value = ({"ok": True, "products": []}, 200)

        response = self.client.get(
            "/api/products", headers={"Authorization": f"Bearer {self.token}"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Cache-Control"), "no-store")
        self.assertEqual(response.get_json(), {"ok": True, "products": []})
        use_case.assert_called_once_with("employee@example.com")

    @patch("backend.src.products.presentation.select_products_by_filter_presentation.search_products_by_text_use_case")
    @patch("backend.src.products.presentation.select_products_by_filter_presentation.select_products_by_filter_use_case")
    def test_search_routes_accept_text_and_combined_filters(
        self, filter_use_case, text_use_case
    ):
        text_use_case.return_value = ({"ok": True, "products": []}, 200)
        filter_use_case.return_value = ({"ok": True, "products": []}, 200)
        headers = {"Authorization": f"Bearer {self.token}"}

        home_response = self.client.get(
            "/api/products/search?query=Dipirona", headers=headers
        )
        combined_response = self.client.get(
            "/api/products/filter?query=Dipirona&branch_id=FIL001", headers=headers
        )
        duplicate_query_response = self.client.get(
            "/api/products/search?query=a&query=b", headers=headers
        )

        self.assertEqual(home_response.status_code, 200)
        self.assertEqual(combined_response.status_code, 200)
        self.assertEqual(duplicate_query_response.status_code, 400)
        text_use_case.assert_called_once_with("Dipirona", "employee@example.com")
        filter_use_case.assert_called_once_with(
            query="Dipirona", branch_id="FIL001", actor_email="employee@example.com"
        )


if __name__ == "__main__":
    unittest.main()
