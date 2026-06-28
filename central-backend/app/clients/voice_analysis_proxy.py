from __future__ import annotations
from urllib.parse import urlencode

import websockets
from app.config import VOICE_ANALYSIS_RESULT_CALLBACK_URL, VOICE_ANALYSIS_WS_URL


class VoiceAnalysisProxy:
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.ws = None

    async def connect(self) -> None:
        query = urlencode({"result_callback_url": VOICE_ANALYSIS_RESULT_CALLBACK_URL})
        url = (
            f"{VOICE_ANALYSIS_WS_URL.rstrip('/')}/ws/voice-analysis/audio/"
            f"{self.session_id}?{query}"
        )
        self.ws = await websockets.connect(url)

    async def send_bytes(self, data: bytes) -> None:
        if self.ws is None:
            raise RuntimeError("VoiceAnalysisProxy websocket is not connected")
        await self.ws.send(data)

    async def close(self) -> None:
        if self.ws is not None:
            await self.ws.close()
            self.ws = None
