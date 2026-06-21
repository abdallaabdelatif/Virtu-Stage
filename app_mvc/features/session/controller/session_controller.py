"""Controller orchestration for session lifecycle use cases."""


class SessionController:
    """Coordinate session creation, retrieval, listing, and ending while using the session repository."""

    async def create_session(self, current_user: object, payload: object) -> object:
        """Validate the create-session use case and persist the new session."""
        ...

    async def get_session(self, session_id: int, current_user: object) -> object:
        """Load the requested session and enforce ownership before returning it."""
        ...

    async def list_sessions(self, current_user: object, limit: int) -> object:
        """Load sessions owned by the authenticated user."""
        ...

    async def end_session(self, session_id: int, current_user: object) -> object:
        """Apply session-ending rules and persist the final session state."""
        ...
