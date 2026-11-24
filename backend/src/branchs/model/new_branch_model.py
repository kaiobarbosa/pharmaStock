BRAZILIAN_STATES = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
    "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
    "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}


def verify_null_fields(nome, cep, logradouro, numero, complemento, bairro, cidade, estado):
    required_values = (nome, cep, logradouro, numero, bairro, cidade, estado)
    if any(not isinstance(value, str) or not value.strip() for value in required_values):
        return False
    return complemento is None or isinstance(complemento, str)


def normalize_cep(cep):
    if not isinstance(cep, str):
        return None

    value = cep.strip()
    if len(value) == 9 and value[5] == "-":
        value = f"{value[:5]}{value[6:]}"

    if len(value) != 8 or not value.isdigit() or value == "00000000":
        return None
    return value


def validar_cep(cep):
    return normalize_cep(cep) is not None


def normalize_branch_data(nome, cep, logradouro, numero, complemento, bairro, cidade, estado):
    fields = {
        "nome": (nome, "Nome da filial"),
        "logradouro": (logradouro, "Logradouro"),
        "numero": (numero, "Número"),
        "bairro": (bairro, "Bairro"),
        "cidade": (cidade, "Cidade"),
        "estado": (estado, "Estado"),
    }
    normalized = {}
    errors = {}

    for key, (value, label) in fields.items():
        if not isinstance(value, str) or not value.strip():
            errors[key] = f"{label} é obrigatório."
        else:
            normalized[key] = value.strip()

    if complemento is None:
        normalized["complemento"] = ""
    elif isinstance(complemento, str):
        normalized["complemento"] = complemento.strip()
    else:
        errors["complemento"] = "Complemento deve ser um texto."

    normalized_cep = normalize_cep(cep)
    if normalized_cep is None:
        errors["cep"] = "Informe um CEP válido com oito dígitos."
    else:
        normalized["cep"] = normalized_cep

    if "estado" in normalized:
        normalized["estado"] = normalized["estado"].upper()
        if normalized["estado"] not in BRAZILIAN_STATES:
            errors["estado"] = "Informe uma sigla de estado válida."

    # Limits match the configured endereco/filial MySQL columns.
    max_lengths = {
        "nome": (50, "Nome da filial"),
        "logradouro": (100, "Logradouro"),
        "numero": (10, "Número"),
        "complemento": (100, "Complemento"),
        "bairro": (100, "Bairro"),
        "cidade": (100, "Cidade"),
    }
    for key, (max_length, label) in max_lengths.items():
        value = normalized.get(key)
        if value is not None and len(value) > max_length:
            errors[key] = f"{label} deve ter no máximo {max_length} caracteres."

    return normalized, errors
