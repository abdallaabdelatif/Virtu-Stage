from openai import AsyncOpenAI

from interfaces.llm_service import ILLMService


class OpenAILLM(ILLMService):

    def __init__(self,api_key: str,model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI(
            api_key=api_key
        )
        self.model = model

    async def generate_response(self,conversation: list[dict]) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=conversation
        )

        return response.choices[0].message.content