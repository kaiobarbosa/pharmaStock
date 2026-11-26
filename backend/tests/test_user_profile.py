import unittest
from unittest.mock import patch

from flask import Flask

from backend.src.login_and_create_account.infrastructure.repository import (
    user_repository,
)
from backend.src.login_and_create_account.model.user_model import (
    validate_user_profile_update,
)
from backend.src.login_and_create_account.presentation.select_user_information_presentation import (
    blueprint_select_user_information,
)
from backend.src.login_and_create_account.presentation.update_user_information_presentation import (
    blueprint_update_user_information,
)
from backend.src.login_and_create_account.use_case.token_use_case import (
    create_user_token,
    decode_user_token,
)
from backend.src.login_and_create_account.use_case import (
    update_user_information_use_case as profile_update_use_case,
)


VALID_UPDATE = {
    "first_name": "Ana",
    "last_name": "Ribeiro",
    "email": "ana.ribeiro@example.com",
    "cpf": "529.982.247-25",
    "current_password": "senha-atual",
}


def profile_row(**overrides):
    row = {
        "id_usuario": "USR001",
        "first_name": "Ana",
        "last_name": "Ribeiro",
        "email": "ana@example.com",
        "cpf": "52998224725",
        "role": "farmaceutico",
        "active": True,
        "internal_code": "FAR00001",
        "crf": "CRF-SP 12345",
        "branch": "Filial Centro",
    }
    row.update(overrides)
    return row


class FakeCursor:
    def __init__(self, row=None, duplicate_at=None):
        self.row = row or profile_row()
        self.duplicate_at = duplicate_at
        self.executed = []
        self.fetchone_count = 0
        self.closed = False

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        self.fetchone_count += 1
        if self.fetchone_count == 1:
            return self.row
        if self.duplicate_at == self.fetchone_count:
            return (1,)
        return None

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


class ProfileModelTests(unittest.TestCase):
    def test_validates_and_normalizes_personal_fields(self):
        normalized, errors = validate_user_profile_update(VALID_UPDATE, "ana@example.com")
        self.assertEqual(errors, {})
        self.assertEqual(normalized["email"], "ana.ribeiro@example.com")
        self.assertEqual(normalized["cpf"], "52998224725")

    def test_requires_current_password_when_email_changes(self):
        data = {key: value for key, value in VALID_UPDATE.items() if key != "current_password"}
        _, errors = validate_user_profile_update(data, "ana@example.com")
        self.assertIn("current_password", errors)

    def test_rejects_invalid_cpf_email_and_uneditable_fields(self):
        data = {
            **VALID_UPDATE,
            "cpf": "111.111.111-11",
            "email": "not-an-email",
            "active": False,
        }
        _, errors = validate_user_profile_update(data, "ana@example.com")
        self.assertIn("cpf", errors)
        self.assertIn("email", errors)
        self.assertIn("fields", errors)

    def test_rejects_non_object_body(self):
        normalized, errors = validate_user_profile_update(
            ["not", "an", "object"], "ana@example.com"
        )
        self.assertEqual(normalized, {})
        self.assertIn("body", errors)


class ProfilePresentationTests(unittest.TestCase):
    def setUp(self):
        self.secret = "test-secret-key-that-is-long-enough"
        self.app = Flask(__name__)
        self.app.config["JWT_SECRET_KEY"] = self.secret
        self.app.register_blueprint(blueprint_select_user_information)
        self.app.register_blueprint(blueprint_update_user_information)
        self.client = self.app.test_client()

    def token(self, email="ana@example.com"):
        return create_user_token("Ana Ribeiro", email, self.secret)

    def test_profile_read_requires_bearer_token_and_disables_caching(self):
        with patch(
            "backend.src.login_and_create_account.presentation."
            "select_user_information_presentation.select_user_information_use_case"
        ) as use_case:
            response = self.client.get("/api/users/me")
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.headers["Cache-Control"], "no-store")
            use_case.assert_not_called()

    def test_profile_read_uses_signed_in_email_not_query_parameter(self):
        with patch(
            "backend.src.login_and_create_account.presentation."
            "select_user_information_presentation.select_user_information_use_case",
            return_value=({"ok": True, "user": {"email": "ana@example.com"}}, 200),
        ) as use_case:
            response = self.client.get(
                "/api/users/me?email=other@example.com",
                headers={"Authorization": f"Bearer {self.token()}"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        use_case.assert_called_once_with("ana@example.com")

    def test_update_uses_token_identity_and_returns_refreshed_token(self):
        new_token = create_user_token("Ana Ribeiro", VALID_UPDATE["email"], self.secret)
        expected = ({"ok": True, "user": {}, "access_token": new_token}, 200)
        with patch(
            "backend.src.login_and_create_account.presentation."
            "update_user_information_presentation.update_user_information_use_case",
            return_value=expected,
        ) as use_case:
            response = self.client.put(
                "/api/users/me",
                json=VALID_UPDATE,
                headers={"Authorization": f"Bearer {self.token()}"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        args = use_case.call_args.args
        self.assertEqual(args[0], VALID_UPDATE)
        self.assertEqual(args[1], "ana@example.com")
        self.assertEqual(args[2], self.secret)
        self.assertEqual(decode_user_token(response.json["access_token"], self.secret)["email"], VALID_UPDATE["email"])

    def test_update_rejects_role_or_status_changes_before_repository(self):
        with patch.object(
            profile_update_use_case,
            "update_user_information_by_email",
        ) as update_repository:
            response = self.client.put(
                "/api/users/me",
                json={**VALID_UPDATE, "role": "diretor", "active": True},
                headers={"Authorization": f"Bearer {self.token()}"},
            )
        self.assertEqual(response.status_code, 400)
        update_repository.assert_not_called()

    def test_update_rejects_invalid_token(self):
        response = self.client.put(
            "/api/users/me",
            json=VALID_UPDATE,
            headers={"Authorization": "Bearer invalid.token.value"},
        )
        self.assertEqual(response.status_code, 401)


class ProfileRepositoryTests(unittest.TestCase):
    def test_update_uses_parameterized_sql_and_token_email_lookup(self):
        cursor = FakeCursor()
        connection = FakeConnection(cursor)
        injected_name = "Ana', ativo = 0 --"
        data = {
            "first_name": injected_name,
            "last_name": VALID_UPDATE["last_name"],
            "email": VALID_UPDATE["email"],
            "cpf": "52998224725",
        }

        with patch.object(user_repository, "conectar_banco", return_value=connection):
            result = user_repository.update_user_information_by_email(
                "signed-in@example.com", data
            )

        self.assertEqual(result["first_name"], injected_name)
        self.assertTrue(connection.committed)
        self.assertFalse(connection.rolled_back)
        self.assertTrue(connection.closed)
        self.assertTrue(cursor.closed)
        select_query, select_params = cursor.executed[0]
        self.assertIn("WHERE u.email_usuario = %s", select_query)
        self.assertEqual(select_params, ("signed-in@example.com",))
        user_update, user_params = next(
            (query, params)
            for query, params in cursor.executed
            if query.lstrip().startswith("UPDATE usuario")
        )
        self.assertIn("nome_usuario = %s", user_update)
        self.assertNotIn(injected_name, user_update)
        self.assertEqual(user_params[0], injected_name)
        self.assertEqual(user_params[-1], "USR001")

    def test_duplicate_email_rolls_back_transaction(self):
        cursor = FakeCursor(duplicate_at=2)
        connection = FakeConnection(cursor)
        with patch.object(user_repository, "conectar_banco", return_value=connection):
            with self.assertRaises(user_repository.DuplicateUserData):
                user_repository.update_user_information_by_email(
                    "signed-in@example.com",
                    {
                        "first_name": VALID_UPDATE["first_name"],
                        "last_name": VALID_UPDATE["last_name"],
                        "email": VALID_UPDATE["email"],
                        "cpf": "52998224725",
                    },
                )
        self.assertTrue(connection.rolled_back)
        self.assertFalse(connection.committed)
        self.assertEqual(len(cursor.executed), 2)

    def test_profile_select_does_not_select_password_hash(self):
        cursor = FakeCursor()
        connection = FakeConnection(cursor)
        with patch.object(user_repository, "conectar_banco", return_value=connection):
            user_repository.select_user_information_by_email("signed-in@example.com")
        query, params = cursor.executed[0]
        self.assertNotIn("senha_funcionario", query)
        self.assertEqual(params, ("signed-in@example.com",))


class ProfileUseCaseTests(unittest.TestCase):
    def test_email_change_with_wrong_password_does_not_update_repository(self):
        with patch.object(
            profile_update_use_case,
            "find_login_user_by_email",
            return_value={"ativo": True, "senha_funcionario": "hash"},
        ), patch.object(profile_update_use_case, "verify_password", return_value=False), patch.object(
            profile_update_use_case, "update_user_information_by_email"
        ) as update_repository:
            response, status = profile_update_use_case.update_user_information_use_case(
                VALID_UPDATE,
                "ana@example.com",
                "test-secret-key-that-is-long-enough",
            )

        self.assertEqual(status, 400)
        self.assertIn("current_password", response["errors"])
        update_repository.assert_not_called()

    def test_successful_update_normalizes_data_and_issues_token_for_new_email(self):
        secret = "test-secret-key-that-is-long-enough"
        updated_row = profile_row(
            first_name="Ana",
            last_name="Ribeiro",
            email="ana.ribeiro@example.com",
            cpf="52998224725",
        )
        with patch.object(
            profile_update_use_case,
            "update_user_information_by_email",
            return_value=updated_row,
        ) as update_repository, patch.object(
            profile_update_use_case,
            "find_login_user_by_email",
            return_value={"ativo": True, "senha_funcionario": "hash"},
        ), patch.object(profile_update_use_case, "verify_password", return_value=True):
            response, status = profile_update_use_case.update_user_information_use_case(
                VALID_UPDATE, "ana@example.com", secret
            )

        self.assertEqual(status, 200)
        self.assertEqual(response["user"]["cpf"], "52998224725")
        update_repository.assert_called_once_with(
            "ana@example.com",
            {
                "first_name": "Ana",
                "last_name": "Ribeiro",
                "email": "ana.ribeiro@example.com",
                "cpf": "52998224725",
            },
        )
        claims = decode_user_token(response["access_token"], secret)
        self.assertEqual(claims["email"], "ana.ribeiro@example.com")
        self.assertEqual(claims["nome"], "Ana Ribeiro")


if __name__ == "__main__":
    unittest.main()
