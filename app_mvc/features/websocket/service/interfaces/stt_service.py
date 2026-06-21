"""Abstract speech-to-text contract used by the conversational controller."""

from abc import ABC, abstractmethod


class STTService(ABC):
    """Define speech-to-text behavior independently from the concrete provider."""

    @abstractmethod
    async def transcribe(self, audio_data: bytes) -> str:
        """Return the final transcript extracted from the supplied audio payload."""
        ...

    @abstractmethod
    async def transcribe_partial(self, audio_data: bytes) -> str:
        """Return a partial transcript for streaming or incremental UI feedback."""
        ...
