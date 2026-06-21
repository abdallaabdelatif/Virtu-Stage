"""Database engine and session lifecycle contracts."""


class DatabaseSessionManager:
    """Manage database engine creation and session lifecycle for dependency injection."""

    def create_engine(self) -> object:
        """Create and configure the database engine for the application."""
        ...

    def create_session_factory(self) -> object:
        """Create the session factory used to open database sessions."""
        ...

    async def get_session(self) -> object:
        """Yield a database session to repositories and request handlers."""
        ...
