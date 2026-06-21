"""Controller orchestration for motion analysis workflows."""


class MotionController:
    """Coordinate motion-analysis use cases and persistence for session-scoped movement events."""

    async def analyze_motion(self, session_id: int, current_user: object, motion_data: object) -> object:
        """Run motion analysis for the supplied movement payload and persist the resulting insight."""
        ...

    async def get_recent_analyses(self, session_id: int, current_user: object) -> object:
        """Return recent motion-analysis records for the supplied session."""
        ...
