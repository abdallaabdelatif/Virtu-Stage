from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.analysis.motion_pipeline import MotionAnalysisPipeline
from app.frame.frame_buffer import FrameBuffer
from app.websocket.result_sender import send_result_to_central_backend

logger = logging.getLogger(__name__)
router = APIRouter()

pipeline = MotionAnalysisPipeline()


@router.websocket("/ws/motion-analysis/frames/{session_id}")
async def frame_socket(websocket: WebSocket, session_id: str) -> None:
    """Production ingress: VR JPEG batches via central-backend proxy."""
    await websocket.accept()
    buffer = FrameBuffer(session_id=session_id)
    logger.info("Motion frame websocket opened for session %s", session_id)

    try:
        while True:
            batch = await websocket.receive_bytes()
            try:
                buffer.add_batch(batch)
            except ValueError:
                logger.warning("Invalid frame batch for session %s", session_id)
    except WebSocketDisconnect:
        logger.info("Motion frame socket closed for session %s", session_id)
    except Exception:
        logger.exception("Motion frame socket error for session %s", session_id)
        return

    if not buffer.has_frames:
        logger.warning("Session %s: no frames received", session_id)
        return

    try:
        result = pipeline.run(session_id, buffer.frames)
        await send_result_to_central_backend(result)
    except Exception:
        logger.exception("Motion analysis failed for session %s", session_id)
