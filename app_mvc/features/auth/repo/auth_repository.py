"""Repository contract for authentication-related persistence operations."""


class AuthRepository:
    """Provide persistence access for user records needed by authentication workflows."""

    async def get_user_by_email(self, email: str) -> object:
        """Return the user record matching the supplied email address."""
        ...

    async def get_user_by_id(self, user_id: int) -> object:
        """Return the user record matching the supplied identifier."""
        ...

    async def create_user(self, payload: object) -> object:
        """Persist a new user record for the registration workflow."""
        ...
