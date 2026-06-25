from __future__ import annotations

import websockets

from app.config import MOTION_ANALYSIS_WS_URL


class MotionAnalysisProxy:
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.ws = None

    async def connect(self) -> None:
        url = (
            f"{MOTION_ANALYSIS_WS_URL.rstrip('/')}"
            f"/ws/motion-analysis/frames/{self.session_id}"
        )
        self.ws = await websockets.connect(url)

    async def send_bytes(self, data: bytes) -> None:
        if self.ws is None:
            raise RuntimeError("MotionAnalysisProxy websocket is not connected")
        await self.ws.send(data)

    async def close(self) -> None:
        if self.ws is not None:
            await self.ws.close()
            self.ws = None
