"""Repository contract for voice analysis persistence."""


class VoiceRepository:
    """Provide persistence operations for voice-analysis results."""

    async def create_analysis(self, session_id: int, user_id: int, payload: object) -> object:
        """Persist a new voice-analysis result for the supplied session."""
        ...

    async def list_by_session(self, session_id: int, limit: int) -> object:
        """Return voice-analysis records associated with the supplied session."""
        ...
