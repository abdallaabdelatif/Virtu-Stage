"""Controller orchestration for voice analysis workflows."""


class VoiceAnalysisController:
    """Coordinate voice-analysis use cases and persistence for session-scoped audio events."""

    async def analyze_audio(self, session_id: int, current_user: object, audio_data: bytes) -> object:
        """Run voice analysis for the supplied audio payload and persist the resulting insight."""
        ...

    async def get_recent_analyses(self, session_id: int, current_user: object) -> object:
        """Return recent voice-analysis records for the supplied session."""
        ...
