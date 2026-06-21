"""REST view definitions for authentication flows."""


class AuthView:
    """Expose authentication endpoints and delegate all business work to the auth controller."""

    async def register(self, payload: object) -> object:
        """Handle user registration requests and return the created user response."""
        ...

    async def login(self, form_data: object) -> object:
        """Handle credential-based login and return an access-token response."""
        ...
