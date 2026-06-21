"""Token creation and validation contracts."""


class TokenSecurity:
    """Provide access-token creation and decoding helpers."""

    def create_access_token(self, subject: str) -> str:
        """Create an access token representing the supplied subject."""
        ...

    def decode_access_token(self, token: str) -> dict:
        """Decode and validate the supplied access token payload."""
        ...
