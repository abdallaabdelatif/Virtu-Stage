"""Controller orchestration for conversational real-time workflows."""


class ConversationalController:
    """Coordinate speech-to-text, AI response generation, text-to-speech, and persistence."""

    async def handle_audio_input(self, session_id: int, current_user: object, audio_data: bytes) -> object:
        """Process inbound audio, generate a response, and return the outbound conversational payload."""
        ...

    async def get_history(self, session_id: int, current_user: object) -> object:
        """Return prior conversational events for the supplied session."""
        ...
