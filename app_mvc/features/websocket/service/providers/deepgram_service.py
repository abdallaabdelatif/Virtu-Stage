"""Deepgram provider adapter for speech-to-text workflows."""


class DeepgramService:
    """Implement the STT service contract using Deepgram APIs."""

    async def transcribe(self, audio_data: bytes) -> str:
        """Send audio to Deepgram and return the final transcript."""
        ...

    async def transcribe_partial(self, audio_data: bytes) -> str:
        """Send audio to Deepgram and return a partial transcript for progressive updates."""
        ...
