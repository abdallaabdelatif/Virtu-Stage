"""OpenAI provider adapter for assistant-response workflows."""


class OpenAIService:
    """Implement the AI response service contract using OpenAI models."""

    async def generate_response(self, transcript: str, context: object) -> str:
        """Generate an assistant reply from transcript and conversation context."""
        ...
