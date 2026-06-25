import json
import websockets

from interfaces.stt_service import ISTTService


class DeepgramSTT(ISTTService):

    def __init__(self,api_key: str,sample_rate: int = 16000,channels: int = 1,
        model: str = "nova-3"
    ):
        self.api_key = api_key
        self.sample_rate = sample_rate
        self.channels = channels
        self.model = model
        self.ws = None

    async def connect(self):
        url = (
            "wss://api.deepgram.com/v1/listen"
            f"?encoding=linear16"
            f"&sample_rate={self.sample_rate}"
            f"&channels={self.channels}"
            f"&model={self.model}"
        )

        self.ws = await websockets.connect(
            url,
            extra_headers={
                "Authorization": f"Token {self.api_key}"
            }
        )

    async def send_audio(self,audio_chunk: bytes):
        await self.ws.send(audio_chunk)

    async def receive_transcript(self):
        while True:
            message = await self.ws.recv()
            if isinstance(message, bytes):
                continue

            try:
                data = json.loads(message)
                if not data.get("is_final", False):
                    continue

                channel = data.get("channel",{})

                alternatives = channel.get("alternatives",[])

                if not alternatives:
                    continue

                transcript = (alternatives[0].get("transcript", "").strip())

                if transcript:
                    return transcript

            except Exception:
                continue

    async def close(self):
        if self.ws:
            await self.ws.close()