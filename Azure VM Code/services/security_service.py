import bcrypt


def hash_pass(code):
    code_bytes = code.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(code_bytes, salt)

    return hashed_password.decode("utf-8")


def verify_pass(code, code_hash):
    code_bytes = code.encode("utf-8")
    hash_bytes = code_hash.encode("utf-8")

    return bcrypt.checkpw(code_bytes, hash_bytes)