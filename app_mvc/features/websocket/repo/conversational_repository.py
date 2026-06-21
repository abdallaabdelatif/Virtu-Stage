"""Repository contract for conversational event persistence."""


class ConversationalRepository:
    """Provide persistence operations for transcripts, responses, and conversation history."""

    async def create_event(self, session_id: int, user_id: int, payload: object) -> object:
        """Persist a new conversational event produced during a WebSocket session."""
        ...

    async def list_by_session(self, session_id: int, limit: int) -> object:
        """Return conversational events associated with the supplied session."""
        ...
