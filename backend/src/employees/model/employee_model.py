import re
import unicodedata

from backend.src.login_and_create_account.model.director_model import (
    normalize_cpf,
    validate_email,
    verify_director_cpf_format,
)


EMPLOYEE_ROLE_ALIASES = {
    "diretor": "diretor",
    "director": "diretor",
    "gerente": "gerente",
    "manager": "gerente",
    "farmaceutico": "farmaceutico",
    "pharmacist": "farmaceutico",
    "atendente": "atendente",
    "attendant": "atendente",
}


def normalize_branch_id(id_filial):
    if not isinstance(id_filial, str):
        return None

    id_filial = id_filial.strip()
    if re.fullmatch(r"[A-Za-z0-9]{6}", id_filial) is None:
        return None
    return id_filial.upper()


def normalize_employee_role(role):
    if not isinstance(role, str):
        return None

    role_key = unicodedata.normalize("NFKD", role.strip().lower())
    role_key = "".join(char for char in role_key if not unicodedata.combining(char))
    return EMPLOYEE_ROLE_ALIASES.get(role_key)


def validate_new_employee_data(data):
    errors = {}
    normalized = {}

    def field(*keys):
        for key in keys:
            if key in data:
                return data.get(key)
        return None

    role_value = field("role", "tipo_usuario")
    normalized_role = normalize_employee_role(role_value)
    if normalized_role is None:
        errors["role"] = "Selecione um cargo válido."
    else:
        normalized["role"] = normalized_role

    required_text_fields = {
        "first_name": (("first_name", "firstName"), "Nome"),
        "last_name": (("last_name", "lastName"), "Sobrenome"),
        "email": (("email",), "E-mail"),
        "password": (("password",), "Senha"),
        "internal_code": (("internal_code", "internalCode"), "Código interno"),
        "cpf": (("cpf",), "CPF"),
    }
    for normalized_key, (input_keys, label) in required_text_fields.items():
        value = field(*input_keys)
        if not isinstance(value, str) or not value.strip():
            errors[input_keys[0]] = f"{label} é obrigatório."
        else:
            normalized[normalized_key] = value if normalized_key == "password" else value.strip()

    if "email" in normalized:
        normalized["email"] = normalized["email"].lower()
        if len(normalized["email"]) > 254 or not validate_email(normalized["email"]):
            errors["email"] = "Informe um endereço de e-mail válido."

    if "cpf" in normalized:
        normalized["cpf"] = normalize_cpf(normalized["cpf"])
        if not verify_director_cpf_format(normalized["cpf"]):
            errors["cpf"] = "Informe um CPF válido."

    if "first_name" in normalized and len(normalized["first_name"]) > 100:
        errors["first_name"] = "Nome deve ter no máximo 100 caracteres."
    if "last_name" in normalized and len(normalized["last_name"]) > 100:
        errors["last_name"] = "Sobrenome deve ter no máximo 100 caracteres."
    if "internal_code" in normalized and len(normalized["internal_code"]) > 8:
        errors["internal_code"] = "Código interno deve ter no máximo 8 caracteres."
    if "password" in normalized and len(normalized["password"].encode("utf-8")) > 72:
        errors["password"] = "A senha deve ter no máximo 72 bytes."

    confirmation = field("password_confirmation", "passwordConfirmation")
    if confirmation is not None:
        if not isinstance(confirmation, str) or confirmation != normalized.get("password"):
            errors["password_confirmation"] = "As senhas não coincidem."

    branch_value = field("branch_id", "branchId", "branch")
    if normalized.get("role") != "diretor":
        if not isinstance(branch_value, str) or not branch_value.strip():
            errors["branch_id"] = "Filial é obrigatória para este cargo."
        elif len(branch_value.strip()) > 50:
            errors["branch_id"] = "Selecione uma filial válida."
        else:
            normalized["branch_reference"] = branch_value.strip()

    if normalized.get("role") == "farmaceutico":
        crf = field("crf")
        if not isinstance(crf, str) or not crf.strip():
            errors["crf"] = "CRF é obrigatório para farmacêuticos."
        elif len(crf.strip()) > 20:
            errors["crf"] = "CRF deve ter no máximo 20 caracteres."
        else:
            normalized["crf"] = crf.strip()
    else:
        normalized["crf"] = "N/A"

    return normalized, errors


def validate_employee_edit_data(data):
    errors = {}
    normalized = {}

    def field(*keys):
        for key in keys:
            if key in data:
                return data.get(key)
        return None

    role = normalize_employee_role(field("role", "tipo_usuario"))
    if role is None:
        errors["role"] = "Selecione um cargo válido."
    else:
        normalized["role"] = role

    for key, aliases, label in (
        ("first_name", ("first_name", "firstName"), "Nome"),
        ("last_name", ("last_name", "lastName"), "Sobrenome"),
        ("email", ("email",), "E-mail"),
    ):
        value = field(*aliases)
        if not isinstance(value, str) or not value.strip():
            errors[key] = f"{label} é obrigatório."
            continue
        normalized[key] = value.strip()

    if "first_name" in normalized and len(normalized["first_name"]) > 100:
        errors["first_name"] = "Nome deve ter no máximo 100 caracteres."
    if "last_name" in normalized and len(normalized["last_name"]) > 100:
        errors["last_name"] = "Sobrenome deve ter no máximo 100 caracteres."
    if "email" in normalized:
        normalized["email"] = normalized["email"].lower()
        if len(normalized["email"]) > 254 or not validate_email(normalized["email"]):
            errors["email"] = "Informe um endereço de e-mail válido."

    branch_value = field("branch_id", "branchId", "branch")
    if normalized.get("role") != "diretor":
        if not isinstance(branch_value, str) or not branch_value.strip():
            errors["branch_id"] = "Filial é obrigatória para este cargo."
        elif len(branch_value.strip()) > 50:
            errors["branch_id"] = "Selecione uma filial válida."
        else:
            normalized["branch_reference"] = branch_value.strip()

    if normalized.get("role") == "farmaceutico":
        crf = field("crf")
        if crf is None or (isinstance(crf, str) and not crf.strip()):
            normalized["crf"] = None
        elif not isinstance(crf, str):
            errors["crf"] = "Informe um CRF válido."
        elif len(crf.strip()) > 20:
            errors["crf"] = "CRF deve ter no máximo 20 caracteres."
        else:
            normalized["crf"] = crf.strip()
    else:
        normalized["crf"] = "N/A"

    return normalized, errors
