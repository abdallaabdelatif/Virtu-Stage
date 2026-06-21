"""Database dependency providers for controllers and repositories."""


class DatabaseDependencies:
    """Provide database-related dependencies to application layers."""

    async def get_db_session(self) -> object:
        """Yield the database session used by repository instances."""
        ...
