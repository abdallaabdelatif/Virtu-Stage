from abc import ABC, abstractmethod


class ILLMService(ABC):

    @abstractmethod
    async def generate_response(self,conversation: list[dict]) -> str:
        pass