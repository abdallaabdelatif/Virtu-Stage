"""Password hashing and verification contracts."""


class PasswordSecurity:
    """Provide password hashing and password verification helpers."""

    def hash_password(self, plain_password: str) -> str:
        """Return a secure hash for the provided plain-text password."""
        ...

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify whether a plain-text password matches the stored hash."""
        ...
