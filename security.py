from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(password: str) -> str:
    """
    Takes a plaintext password and returns a secure, one-way hash.
    """
    return generate_password_hash(password)


def verify_password(stored_hash: str, candidate_password: str) -> bool:
    """
    Checks if the candidate password matches the stored hash.
    Returns True if they match, False otherwise.
    """
    return check_password_hash(stored_hash, candidate_password)