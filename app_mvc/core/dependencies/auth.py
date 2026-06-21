"""Authentication and authorization dependencies shared across features."""


class AuthDependencies:
    """Provide authenticated-user and authorization dependencies."""

    async def get_current_user(self) -> object:
        """Resolve the current authenticated user from the incoming request context."""
        ...

    async def get_current_active_user(self) -> object:
        """Resolve the current authenticated and active user."""
        ...

    async def get_current_superuser(self) -> object:
        """Resolve the current authenticated user with elevated privileges."""
        ...
