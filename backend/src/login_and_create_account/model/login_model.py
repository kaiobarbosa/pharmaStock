def verify_user_null_fields(email, password):
    return (
        isinstance(email, str)
        and bool(email.strip())
        and isinstance(password, str)
        and bool(password.strip())
    )
