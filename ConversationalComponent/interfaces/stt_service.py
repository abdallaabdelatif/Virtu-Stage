from abc import ABC, abstractmethod


class ISTTService(ABC):

    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def send_audio(self,audio_chunk: bytes):
        pass

    @abstractmethod
    async def receive_transcript(self):
        pass

    @abstractmethod
    async def close(self):
        pass