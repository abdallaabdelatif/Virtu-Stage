"""Repository contract for motion analysis persistence."""


class MotionRepository:
    """Provide persistence operations for motion-analysis results."""

    async def create_analysis(self, session_id: int, user_id: int, payload: object) -> object:
        """Persist a new motion-analysis result for the supplied session."""
        ...

    async def list_by_session(self, session_id: int, limit: int) -> object:
        """Return motion-analysis records associated with the supplied session."""
        ...
