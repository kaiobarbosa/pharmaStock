def verify_director_null_fields(nome, sobrenome, cpf, email, senha, codigo_interno):
    if not nome or not sobrenome or not cpf or not email or not senha or not codigo_interno:
        return False
    return True

def verify_director_cpf_format(cpf):
    if len(cpf) != 11 or not cpf.isdigit():

        return False
    return True

def validate_email(email):

    if not isinstance(email, str):
        return False

    if " " in email:
        return False

    if email.count("@") != 1:
        return False

    usuario, dominio = email.split("@")

    if not usuario or not dominio:
        return False

    if len(email) > 254 or len(usuario) > 64:
        return False

    if ".." in email:
        return False

    if usuario.startswith(".") or usuario.endswith("."):
        return False

    caracteres_usuario = (
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789"
        "!#$%&'*+-/=?^_`{|}~."
    )

    for caractere in usuario:
        if caractere not in caracteres_usuario:
            return False

    if "." not in dominio:
        return False

    if dominio.startswith(".") or dominio.endswith("."):
        return False

    partes = dominio.split(".")

    for parte in partes:

        if not parte:
            return False

        if parte.startswith("-") or parte.endswith("-"):
            return False

        for caractere in parte:
            if not (
                caractere.isalnum() or caractere == "-"
            ):
                return False

    if len(partes[-1]) < 2:
        return False

    return True
