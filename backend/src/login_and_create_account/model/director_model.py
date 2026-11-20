import re


def normalize_cpf(cpf):
    if not isinstance(cpf, str):
        return ""
    return re.sub(r"\D", "", cpf)


def verify_director_null_fields(nome, sobrenome, cpf, email, senha, codigo_interno):
    values = (nome, sobrenome, cpf, email, senha, codigo_interno)
    return all(isinstance(value, str) and value.strip() for value in values)


def verify_director_cpf_format(cpf):
    cpf = normalize_cpf(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    for length in (9, 10):
        total = sum(int(cpf[index]) * (length + 1 - index) for index in range(length))
        digit = (total * 10) % 11
        if digit == 10:
            digit = 0
        if digit != int(cpf[length]):
            return False
    return True


def validate_email(email):
    if not isinstance(email, str):
        return False
    email = email.strip()
    if len(email) > 254:
        return False
    return re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) is not None
