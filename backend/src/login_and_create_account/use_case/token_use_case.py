from datetime import datetime, timedelta, timezone

import jwt


TOKEN_LIFETIME = timedelta(hours=1)


def create_user_token(name, email, secret_key):
    now = datetime.now(timezone.utc)
    claims = {
        "nome": name,
        "email": email,
        "exp": now + TOKEN_LIFETIME,
    }
    return jwt.encode(claims, secret_key, algorithm="HS256")


def decode_user_token(token, secret_key):
    return jwt.decode(
        token,
        secret_key,
        algorithms=["HS256"],
        options={"require": ["nome", "email", "exp"]},
    )
