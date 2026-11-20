import bcrypt


def verify_password(password, stored_hash):
    if isinstance(stored_hash, dict):
        stored_hash = stored_hash.get("senha_funcionario")
    if not isinstance(password, str) or not isinstance(stored_hash, str):
        return False

    try:
        return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False
