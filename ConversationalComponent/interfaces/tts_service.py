from abc import ABC, abstractmethod


class ITTSService(ABC):

    @abstractmethod
    async def stream_audio(self,text: str):
        pass