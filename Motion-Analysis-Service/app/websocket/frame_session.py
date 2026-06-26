from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.analysis.motion_pipeline import MotionAnalysisPipeline
from app.frame.frame_buffer import FrameBuffer
from app.frame.vr_batch import decode_vr_frame_batch
from app.models.motion_frame_data import MotionFrameData
from app.visualization.live_preview import LivePreview
from app.visualization.preview_frame import PreviousFrameHolder, preview_vr_frames
from app.websocket.result_sender import send_result_to_central_backend

logger = logging.getLogger(__name__)


async def handle_frame_session(
    websocket: WebSocket,
    session_id: str,
    *,
    live_preview: bool = True,
    post_result: bool = True,
) -> None:
    await websocket.accept()
    buffer = FrameBuffer(session_id=session_id)
    pipeline = MotionAnalysisPipeline()
    preview = LivePreview() if live_preview else None
    motion_frames: list[MotionFrameData] = []
    previous = PreviousFrameHolder()

    logger.info(
        "Motion frame websocket opened for session %s (live_preview=%s)",
        session_id,
        live_preview,
    )

    try:
        try:
            while True:
                batch = await websocket.receive_bytes()
                try:
                    vr_frames = decode_vr_frame_batch(batch)
                    buffer.add_batch(batch)
                    if preview is not None:
                        preview_vr_frames(
                            pipeline,
                            preview,
                            vr_frames,
                            buffer.frames,
                            motion_frames,
                            previous,
                        )
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

        if motion_frames:
            fps = MotionAnalysisPipeline._estimate_fps(buffer.frames)
            result = pipeline.run_from_motion_frames(
                session_id, motion_frames, fps=fps
            )
        else:
            result = pipeline.run(session_id, buffer.frames)
        if post_result:
            await send_result_to_central_backend(result)
    except Exception:
        logger.exception("Motion analysis failed for session %s", session_id)
    finally:
        if preview is not None:
            preview.close()
        pipeline.close()


def create_frame_router(*, live_preview: bool = True) -> APIRouter:
    router = APIRouter()

    @router.websocket("/ws/motion-analysis/frames/{session_id}")
    async def frame_socket(websocket: WebSocket, session_id: str) -> None:
        await handle_frame_session(websocket, session_id, live_preview=live_preview)

    return router
