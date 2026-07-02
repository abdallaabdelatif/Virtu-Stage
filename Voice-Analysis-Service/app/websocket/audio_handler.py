# Audio websocket endpoint which receives streamed raw PCM audio chunks for a session

from __future__ import annotations
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.audio.audio_buffer import AudioBuffer
from app.websocket.session_completion import (
    on_audio_socket_closed,
    register_result_callback,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/voice-analysis/audio/{session_id}")
async def audio_socket(
    websocket: WebSocket,
    session_id: str,
) -> None:
    await websocket.accept()
    await register_result_callback(session_id)
    buffer = AudioBuffer(session_id=session_id)
    logger.info("Audio websocket opened for session %s", session_id)

    try:
        while True:
            chunk = await websocket.receive_bytes()
            buffer.add_chunk(chunk)

    except WebSocketDisconnect:
        logger.info(
            "Audio socket closed for session %s, Starting audio analysis",
            session_id,
        )
        await on_audio_socket_closed(session_id, buffer)
