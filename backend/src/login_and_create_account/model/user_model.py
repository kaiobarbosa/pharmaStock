from backend.src.login_and_create_account.model.director_model import (
    normalize_cpf,
    validate_email,
    verify_director_cpf_format,
)


PROFILE_EDITABLE_FIELDS = {
    "first_name",
    "last_name",
    "email",
    "cpf",
    "current_password",
}


def validate_user_profile_update(data, actor_email):
    """Validate the personal fields a signed-in user may edit."""
    if not isinstance(data, dict):
        return {}, {"body": "O corpo JSON enviado é inválido."}

    errors = {}
    unexpected_fields = set(data) - PROFILE_EDITABLE_FIELDS
    if unexpected_fields:
        errors["fields"] = "A edição do perfil contém campos não permitidos."

    normalized = {}
    for key, label, max_length in (
        ("first_name", "Nome", 100),
        ("last_name", "Sobrenome", 100),
        ("email", "E-mail", 254),
        ("cpf", "CPF", 20),
    ):
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            errors[key] = f"{label} é obrigatório."
            continue
        normalized[key] = value.strip()
        if len(normalized[key]) > max_length:
            errors[key] = f"{label} excede o tamanho permitido."

    if "email" in normalized:
        normalized["email"] = normalized["email"].lower()
        try:
            normalized["email"].encode("utf-8")
        except UnicodeEncodeError:
            errors["email"] = "Informe um endereço de e-mail válido."
        if not validate_email(normalized["email"]):
            errors["email"] = "Informe um endereço de e-mail válido."

    current_password = data.get("current_password")
    if current_password not in (None, ""):
        if not isinstance(current_password, str):
            errors["current_password"] = "Informe a senha atual para confirmar."
        else:
            try:
                password_size = len(current_password.encode("utf-8"))
            except UnicodeEncodeError:
                password_size = 73
            if password_size > 72:
                errors["current_password"] = "A senha atual informada é inválida."
            else:
                normalized["current_password"] = current_password

    if (
        "email" in normalized
        and isinstance(actor_email, str)
        and normalized["email"] != actor_email.strip().lower()
    ):
        if not isinstance(current_password, str) or not current_password:
            errors["current_password"] = (
                "Informe sua senha atual para alterar o e-mail."
            )
        elif "current_password" in errors:
            pass
        else:
            normalized["current_password"] = current_password

    if "cpf" in normalized:
        normalized["cpf"] = normalize_cpf(normalized["cpf"])
        if not verify_director_cpf_format(normalized["cpf"]):
            errors["cpf"] = "Informe um CPF válido."

    return normalized, errors


def profile_response(user):
    """Return only profile data intended for the current user interface."""
    return {
        "first_name": user.get("first_name", ""),
        "last_name": user.get("last_name", ""),
        "email": user.get("email", ""),
        "cpf": user.get("cpf", ""),
        "role": user.get("role", ""),
        "branch": user.get("branch") or "—",
        "internal_code": user.get("internal_code") or "—",
        "crf": user.get("crf") or "—",
    }
