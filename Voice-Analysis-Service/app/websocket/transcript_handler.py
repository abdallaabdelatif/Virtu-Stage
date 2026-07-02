# Transcript websocket endpoint which receives streamed transcript text fragments for a session

from __future__ import annotations
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.audio.transcript_buffer import TranscriptBuffer
from app.websocket.session_completion import (
    on_transcript_socket_closed,
    register_result_callback,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/voice-analysis/transcript/{session_id}")
async def transcript_socket(
    websocket: WebSocket,
    session_id: str,
) -> None:
    await websocket.accept()
    await register_result_callback(session_id)
    buffer = TranscriptBuffer(session_id=session_id)
    logger.info("Transcript websocket opened for session %s", session_id)

    try:
        while True:
            raw_text = await websocket.receive_text()
            _handle_message(buffer, raw_text)

    except WebSocketDisconnect:
        logger.info(
            "Transcript socket closed for session %s, Starting transcript analysis",
            session_id,
        )
        await on_transcript_socket_closed(session_id, buffer)


# The expected json fromat: {"type": "transcript", "text": "the real transcriped user speech"}
def _handle_message(buffer: TranscriptBuffer, raw_text: str) -> None:
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        logger.warning("Received non-json transcript message")
        return

    if payload.get("type") == "transcript":
        buffer.add_fragment(payload.get("text", ""))
