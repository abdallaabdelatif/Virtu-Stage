"""Repository contract for session persistence operations."""


class SessionRepository:
    """Provide persistence access for session lifecycle operations."""

    async def create(self, owner_id: int, payload: object) -> object:
        """Persist a newly created session for the supplied owner."""
        ...

    async def get_by_id(self, session_id: int) -> object:
        """Return the session identified by the supplied session ID."""
        ...

    async def get_by_owner(self, owner_id: int, limit: int) -> object:
        """Return sessions belonging to the supplied owner."""
        ...

    async def end(self, session_id: int, owner_id: int) -> object:
        """Persist the ended state for a session owned by the supplied user."""
        ...
