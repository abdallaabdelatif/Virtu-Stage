"""ElevenLabs provider adapter for text-to-speech workflows."""


class ElevenLabsService:
    """Implement the TTS service contract using ElevenLabs APIs."""

    async def synthesize(self, text: str) -> bytes:
        """Generate synthesized speech audio for the supplied text."""
        ...
