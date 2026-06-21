"""REST view definitions for session lifecycle endpoints."""


class SessionView:
    """Expose session lifecycle endpoints and delegate orchestration to the session controller."""

    async def create_session(self, payload: object, current_user: object) -> object:
        """Create a new session for the authenticated user."""
        ...

    async def get_session(self, session_id: int, current_user: object) -> object:
        """Return the requested session if it belongs to the authenticated user."""
        ...

    async def end_session(self, session_id: int, current_user: object) -> object:
        """End an active session owned by the authenticated user."""
        ...

    async def list_sessions(self, current_user: object, limit: int) -> object:
        """Return the authenticated user's sessions using the configured paging rules."""
        ...
