import json
import base64
import websockets

from interfaces.tts_service import ITTSService


class ElevenLabsTTS(ITTSService):

    def __init__(self,api_key: str,voice_id: str):
        self.api_key = api_key
        self.voice_id = voice_id

    async def stream_audio(
        self,
        text: str
    ):

        url = (
            f"wss://api.elevenlabs.io/v1/text-to-speech/"
            f"{self.voice_id}/stream-input"
            f"?output_format=pcm_16000"
            f"&model_id=eleven_turbo_v2_5"
        )

        async with websockets.connect(
            url,
            extra_headers={
                "xi-api-key": self.api_key
            }
        ) as ws:

            await ws.send(
                json.dumps(
                    {
                        "text": " ",
                        "voice_settings": {
                            "stability": 0.5,
                            "similarity_boost": 0.8,
                            "speed": 1.0
                        },
                        "xi_api_key": self.api_key
                    }
                )
            )

            await ws.send(
                json.dumps(
                    {
                        "text": text,
                        "try_trigger_generation": True
                    }
                )
            )

            await ws.send(
                json.dumps(
                    {
                        "text": ""
                    }
                )
            )

            while True:

                message = await ws.recv()

                if isinstance(message,bytes):
                    continue

                payload = json.loads(message)

                audio = payload.get("audio")

                if audio:
                    yield base64.b64decode(audio)

                if payload.get("isFinal"):
                    break