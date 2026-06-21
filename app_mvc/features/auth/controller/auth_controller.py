"""Controller orchestration for authentication use cases."""


class AuthController:
    """Coordinate authentication use cases between the auth view, auth service, and shared policies."""

    async def register_user(self, payload: object) -> object:
        """Validate the registration use case and delegate user creation to the auth service."""
        ...

    async def authenticate_user(self, identity: str, password: str) -> object:
        """Validate credentials and orchestrate token issuance for a successful login."""
        ...
