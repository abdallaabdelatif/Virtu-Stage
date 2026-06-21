"""Abstract text-to-speech contract used by the conversational controller."""

from abc import ABC, abstractmethod


class TTSService(ABC):
    """Define text-to-speech behavior independently from the concrete provider."""

    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """Return synthesized audio for the supplied assistant text."""
        ...
