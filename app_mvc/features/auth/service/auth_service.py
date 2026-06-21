"""Service layer for authentication rules and token lifecycle management."""


class AuthService:
    """Encapsulate authentication business rules while using the auth repository for persistence."""

    async def register_user(self, payload: object) -> object:
        """Apply registration rules, hash credentials, and create the new user through the repository."""
        ...

    async def verify_credentials(self, identity: str, password: str) -> object:
        """Validate user credentials and return the authenticated user on success."""
        ...

    def issue_access_token(self, subject: str) -> str:
        """Issue a signed access token for the authenticated subject."""
        ...
