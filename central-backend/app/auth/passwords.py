import base64
import hashlib
import hmac


def verify_password_with_crud_hash(plain_password: str, stored_hash_b64: str) -> bool:
    """Verify password using CRUD module's hash format: base64(salt(32) + digest).

    CRUD uses: salt = os.urandom(32); digest = pbkdf2_hmac('sha256', password, salt, 100000)
    and stores base64(salt + digest)
    """
    try:
        decoded = base64.b64decode(stored_hash_b64)
    except Exception:
        return False

    if len(decoded) <= 32:
        return False

    salt = decoded[:32]
    digest = decoded[32:]

    new_digest = hashlib.pbkdf2_hmac("sha256", plain_password.encode(), salt, 100_000)
    return hmac.compare_digest(new_digest, digest)
