import bcrypt

def verify_password(password, data):

    email = data['email']

    password_from_db = verify_password(email)
    
    password_bytes = password.encode("utf-8")
    hashed_password_bytes = password_from_db.encode("utf-8")

    return bcrypt.checkpw(password_bytes, hashed_password_bytes)