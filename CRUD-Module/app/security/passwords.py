import base64
import hashlib
import hmac
import os
import re


def hash_password(password: str) -> str:
    salt = os.urandom(32)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt, 100_000
    )
    return base64.b64encode(salt + digest).decode()


def verify_password(plain_password: str, stored_hash_b64: str) -> bool:
    try:
        decoded = base64.b64decode(stored_hash_b64)
    except Exception:
        return False
    if len(decoded) <= 32:
        return False
    salt = decoded[:32]
    digest = decoded[32:]
    candidate = hashlib.pbkdf2_hmac(
        "sha256", plain_password.encode(), salt, 100_000
    )
    return hmac.compare_digest(candidate, digest)


def validate_password_strength(password: str) -> None:
    checks = (
        len(password) >= 8,
        bool(re.search(r"[A-Z]", password)),
        bool(re.search(r"[a-z]", password)),
        bool(re.search(r"\d", password)),
        bool(re.search(r"[^A-Za-z0-9]", password)),
    )
    if not all(checks):
        raise ValueError(
            "Password must be at least 8 characters and include uppercase, "
            "lowercase, number, and special character"
        )
