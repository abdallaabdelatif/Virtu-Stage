"""Abstract voice-analysis contract used by the voice-analysis controller."""

from abc import ABC, abstractmethod


class VoiceAnalysisService(ABC):
    """Define voice-analysis behavior independently from the concrete provider."""

    @abstractmethod
    async def analyze(self, audio_data: bytes) -> object:
        """Return a voice-analysis result for the supplied audio payload."""
        ...
