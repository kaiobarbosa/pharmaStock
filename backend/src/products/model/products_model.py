import re
import unicodedata
from decimal import Decimal, InvalidOperation


PRODUCT_TYPE_ALIASES = {
    "general": "general",
    "geral": "general",
    "produto": "general",
    "dermocosmetic": "dermocosmetic",
    "dermocosmetico": "dermocosmetic",
    "dermocosmeticos": "dermocosmetic",
    "medicine": "medicine",
    "medicamento": "medicine",
    "medicamentos": "medicine",
    "equipment": "equipment",
    "equipamento": "equipment",
    "equipamentos": "equipment",
}


def _fold(value):
    value = unicodedata.normalize("NFKD", value.strip().lower())
    return "".join(char for char in value if not unicodedata.combining(char))


def _field(data, *keys):
    for key in keys:
        if key in data:
            return data[key]
    return None


def _required_text(data, normalized, errors, key, label, max_length, *aliases):
    value = _field(data, key, *aliases)
    if not isinstance(value, str) or not value.strip():
        errors[key] = f"{label} é obrigatório."
        return

    value = value.strip()
    if len(value) > max_length:
        errors[key] = f"{label} deve ter no máximo {max_length} caracteres."
        return
    normalized[key] = value


def _required_choice(data, normalized, errors, key, label, choices, *aliases):
    value = _field(data, key, *aliases)
    if not isinstance(value, str) or not value.strip():
        errors[key] = f"{label} é obrigatório."
        return

    choice = choices.get(_fold(value))
    if choice is None:
        errors[key] = f"Selecione uma opção válida para {label.lower()}."
        return
    normalized[key] = choice


def validate_new_product_data(data):
    """Validate and normalize the base product and its selected category fields."""
    errors = {}
    normalized = {}
    if not isinstance(data, dict):
        return normalized, {"body": "O corpo JSON enviado é inválido."}

    product_type_value = _field(data, "type", "product_type", "tipo_produto", "tipo")
    if not isinstance(product_type_value, str):
        errors["type"] = "Selecione um tipo de produto válido."
    else:
        product_type = PRODUCT_TYPE_ALIASES.get(_fold(product_type_value))
        if product_type is None:
            errors["type"] = "Selecione um tipo de produto válido."
        else:
            normalized["type"] = product_type

    for key, label, max_length, aliases in (
        ("name", "Nome", 100, ("nome_produto",)),
        ("brand", "Marca", 100, ("marca",)),
        ("description", "Descrição", 255, ("descricao",)),
    ):
        _required_text(data, normalized, errors, key, label, max_length, *aliases)

    price = _field(data, "price", "preco")
    if isinstance(price, bool) or price is None:
        errors["price"] = "Preço é obrigatório e deve ser um número válido."
    else:
        price_text = str(price).strip().replace(",", ".")
        if re.fullmatch(r"\d{1,17}(?:\.\d{1,2})?", price_text) is None:
            errors["price"] = "Informe um preço não negativo com até duas casas decimais."
        else:
            try:
                price_value = Decimal(price_text)
            except InvalidOperation:
                errors["price"] = "Informe um preço válido."
            else:
                if not price_value.is_finite():
                    errors["price"] = "Informe um preço válido."
                else:
                    normalized["price"] = format(price_value.quantize(Decimal("0.01")), ".2f")

    barcode = _field(data, "barcode", "codigo_de_barras", "codigo_barras")
    if not isinstance(barcode, str) or not barcode.strip():
        errors["barcode"] = "Código de barras é obrigatório."
    else:
        barcode = barcode.strip()
        if re.fullmatch(r"\d{1,20}", barcode) is None:
            errors["barcode"] = "Informe um código de barras com até 20 dígitos."
        else:
            normalized["barcode"] = barcode

    quantity = _field(data, "quantity", "quantidade")
    if isinstance(quantity, bool) or quantity is None:
        errors["quantity"] = "Quantidade é obrigatória e deve ser um número inteiro."
    else:
        quantity_text = str(quantity).strip()
        if re.fullmatch(r"\d{1,10}", quantity_text) is None:
            errors["quantity"] = "Informe uma quantidade inteira não negativa."
        else:
            normalized["quantity"] = quantity_text

    branch_id = _field(data, "branch", "branch_id", "id_filial")
    if not isinstance(branch_id, str) or re.fullmatch(r"[A-Za-z0-9]{6}", branch_id.strip()) is None:
        errors["branch"] = "Selecione uma filial válida."
    else:
        normalized["branch_id"] = branch_id.strip().upper()

    product_type = normalized.get("type")
    if product_type == "medicine":
        for key, label, max_length, aliases in (
            ("activeIngredient", "Princípio ativo", 50, ("active_ingredient", "principio_ativo")),
            ("pharmaceuticalForm", "Forma farmacêutica", 50, ("pharmaceutical_form", "forma_farmaceutica")),
            ("concentration", "Concentração", 50, ("concentracao",)),
            ("classification", "Tipagem", 50, ("tipagem",)),
        ):
            _required_text(data, normalized, errors, key, label, max_length, *aliases)

        _required_choice(
            data,
            normalized,
            errors,
            "prescriptionBand",
            "Tarja",
            {
                "sem tarja": "Sem Tarja",
                "tarja vermelha": "Tarja Vermelha",
                "tarja preta": "Tarja Preta",
            },
            "prescription_band",
            "tarja",
        )
        prescription = _field(data, "prescriptionRequired", "prescription_required", "receita")
        if isinstance(prescription, bool):
            normalized["prescriptionRequired"] = prescription
        elif isinstance(prescription, (str, int)):
            prescription_value = _fold(str(prescription))
            if prescription_value in ("sim", "yes", "true", "1"):
                normalized["prescriptionRequired"] = True
            elif prescription_value in ("nao", "no", "false", "0"):
                normalized["prescriptionRequired"] = False
            else:
                errors["prescriptionRequired"] = "Informe se o medicamento exige receita."
        else:
            errors["prescriptionRequired"] = "Informe se o medicamento exige receita."

    elif product_type == "dermocosmetic":
        for key, label, max_length, aliases in (
            ("skinType", "Tipo de pele", 100, ("skin_type", "tipo_pele")),
            ("volume", "Volume", 50, ()),
            ("sunProtectionFactor", "Fator de proteção", 50, ("sun_protection_factor", "fator_protecao")),
            ("indication", "Indicação", 20, ("indicacao",)),
        ):
            _required_text(data, normalized, errors, key, label, max_length, *aliases)

    elif product_type == "equipment":
        for key, label, max_length, aliases in (
            ("model", "Modelo", 50, ("modelo",)),
            ("manufacturer", "Fabricante", 50, ("fabricante",)),
            ("specifications", "Especificações", 100, ("especificacoes",)),
            ("warranty", "Garantia", 50, ("garantia",)),
        ):
            _required_text(data, normalized, errors, key, label, max_length, *aliases)

    return normalized, errors


def validate_product_search_filters(
    query=None,
    branch_id=None,
    require_query=False,
    require_filter=False,
):
    """Validate the bounded text and optional branch filters for catalog searches."""
    normalized = {}
    errors = {}

    if query is not None:
        if not isinstance(query, str):
            errors["query"] = "Informe um texto válido para a pesquisa."
        else:
            query = query.strip()
            if query and len(query) > 100:
                errors["query"] = "A pesquisa deve ter no máximo 100 caracteres."
            elif query:
                normalized["query"] = query

    if branch_id is not None:
        if not isinstance(branch_id, str):
            errors["branch_id"] = "Selecione uma filial válida."
        else:
            branch_id = branch_id.strip()
            if branch_id and branch_id.lower() != "all":
                if re.fullmatch(r"[A-Za-z0-9]{6}", branch_id) is None:
                    errors["branch_id"] = "Selecione uma filial válida."
                else:
                    normalized["branch_id"] = branch_id.upper()

    if require_query and not normalized.get("query"):
        errors.setdefault("query", "Digite o nome, princípio ativo ou código do produto.")
    if require_filter and not normalized.get("query") and not normalized.get("branch_id"):
        errors["filters"] = "Informe um texto ou selecione uma filial para pesquisar."

    return normalized, errors
