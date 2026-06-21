"""Abstract AI-response contract used by the conversational controller."""

from abc import ABC, abstractmethod


class AIResponseService(ABC):
    """Define assistant-response generation behavior independently from the concrete provider."""

    @abstractmethod
    async def generate_response(self, transcript: str, context: object) -> str:
        """Return the assistant response generated from the transcript and conversation context."""
        ...
