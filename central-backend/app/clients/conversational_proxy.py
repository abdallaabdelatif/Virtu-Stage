from __future__ import annotations
import json
import websockets
from app.config import CONVERSATIONAL_COMPONENT_WS_URL


class ConversationalProxy:
    def __init__(self, session_id: str, mode: int, job: str | None) -> None:
        self.session_id = session_id
        self.mode = mode
        self.job = job or ""
        self.ws = None

    async def connect(self) -> None:
        self.ws = await websockets.connect(CONVERSATIONAL_COMPONENT_WS_URL)
        await self.send_text(json.dumps({"type": "set_mode", "mode": self.mode}))
        if self.job:
            await self.send_text(json.dumps({"type": "set_job", "job": self.job}))
        
        await self.send_text(json.dumps({"type": "set_session", "sessionId": self.session_id}))

    async def send_text(self, data: str) -> None:
        if self.ws is None:
            raise RuntimeError("ConversationalProxy websocket is not connected")
        await self.ws.send(data)

    async def send_bytes(self, data: bytes) -> None:
        if self.ws is None:
            raise RuntimeError("ConversationalProxy websocket is not connected")
        await self.ws.send(data)

    async def receive_message(self) -> str | bytes:
        if self.ws is None:
            raise RuntimeError("ConversationalProxy websocket is not connected")
        return await self.ws.recv()

    async def close(self) -> None:
        if self.ws is not None:
            await self.ws.close()
            self.ws = None
