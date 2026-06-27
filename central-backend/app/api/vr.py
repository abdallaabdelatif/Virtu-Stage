import asyncio
import contextlib
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status
from app.api.schemas.vr import (
    VRSessionCreate,
    VRAudioControlMessage,
    VoiceAnalysisResultPayload,
    MotionAnalysisResultPayload,
)
from app.clients.voice_analysis_proxy import VoiceAnalysisProxy
from app.clients.conversational_proxy import ConversationalProxy
from app.clients.motion_analysis_proxy import MotionAnalysisProxy
from app.clients.crud_client import crud_client
from app.config import VR_DEFAULT_USER_ID

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["vr"])

session_store: dict[str, dict] = {}


def _scenario_from_mode(mode: int) -> str:
    return "public_speaking" if mode == 2 else "interview"


def _cleanup_session(session_id: str) -> None:
    session = session_store.get(session_id)
    if session is None:
        return

    active_streams = session.get("active_streams", {})
    if active_streams.get("audio", False) or active_streams.get("frames", False):
        return

    session_store.pop(session_id, None)


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def create_session(payload: VRSessionCreate):
    session_id = payload.session_id
    if session_id in session_store:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Session already exists"
        )

    session_store[session_id] = {
        "mode": payload.mode,
        "job": payload.job,
        "user_id": payload.user_id,
        "voice_proxy": None,
        "conv_proxy": None,
        "motion_proxy": None,
    }

    user_id = payload.user_id or VR_DEFAULT_USER_ID
    if user_id:
        try:
            await crud_client.create_training_session(
                {
                    "session_id": session_id,
                    "user_id": user_id,
                    "scenario_type": _scenario_from_mode(payload.mode),
                    "difficulty_level": "medium",
                }
            )
        except Exception:
            logger.exception(
                "Could not create CRUD training session for VR session %s", session_id
            )

    return {"session_id": session_id}


@router.post("/voice-analyses", status_code=status.HTTP_201_CREATED)
async def ingest_voice_analysis(payload: VoiceAnalysisResultPayload):
    stored = await crud_client.create_voice_analysis(payload.to_model_dict())
    return stored


@router.post("/motion-analyses", status_code=status.HTTP_201_CREATED)
async def ingest_motion_analysis(payload: MotionAnalysisResultPayload):
    stored = await crud_client.create_motion_analysis(payload.model_dump())
    return stored


@router.websocket("/ws/vr/audio/{session_id}")
async def vr_audio_socket(websocket: WebSocket, session_id: str):
    await websocket.accept()

    session = session_store.get(session_id)
    if session is None:
        await websocket.close(code=1008)
        return

    session.setdefault("active_streams", {"audio": False, "frames": False})
    session["active_streams"]["audio"] = True

    voice_proxy = VoiceAnalysisProxy(session_id=session_id)
    conv_proxy = ConversationalProxy(
        session_id=session_id, mode=session["mode"], job=session["job"]
    )

    session["voice_proxy"] = voice_proxy
    session["conv_proxy"] = conv_proxy

    async def forward_conv_to_vr() -> None:
        try:
            while True:
                msg = await conv_proxy.receive_message()
                if isinstance(msg, str):
                    await websocket.send_text(msg)
                else:
                    await websocket.send_bytes(msg)
        except WebSocketDisconnect:
            pass
        except Exception:
            pass

    try:
        await voice_proxy.connect()
        await conv_proxy.connect()

        receive_task = asyncio.create_task(forward_conv_to_vr())

        while True:
            message = await websocket.receive()
            if message.get("text") is not None:
                raw_text = message["text"]
                data = json.loads(raw_text)
                msg_type = data.get("type")

                if msg_type == "set_mode":
                    control = VRAudioControlMessage(**data)
                    session["mode"] = control.mode or session["mode"]
                    await conv_proxy.send_text(raw_text)
                elif msg_type == "set_job":
                    control = VRAudioControlMessage(**data)
                    session["job"] = control.job or session["job"]
                    await conv_proxy.send_text(raw_text)
                elif msg_type == "audio_end":
                    await conv_proxy.send_text(raw_text)
                    await voice_proxy.close()
                elif msg_type in {"generate_question", "audio_start"}:
                    await conv_proxy.send_text(raw_text)
                else:
                    await conv_proxy.send_text(raw_text)

            elif message.get("bytes") is not None:
                chunk = message["bytes"]
                await voice_proxy.send_bytes(chunk)
                await conv_proxy.send_bytes(chunk)
            else:
                break

        receive_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await receive_task
    except WebSocketDisconnect:
        pass
    finally:
        session["active_streams"]["audio"] = False
        if voice_proxy.ws is not None:
            await voice_proxy.close()
        await conv_proxy.close()
        _cleanup_session(session_id)


@router.websocket("/ws/vr/frames/{session_id}")
async def vr_frame_socket(websocket: WebSocket, session_id: str):
    await websocket.accept()
    session = session_store.get(session_id)
    if session is None:
        await websocket.close(code=1008)
        return

    session.setdefault("active_streams", {"audio": False, "frames": False})
    session["active_streams"]["frames"] = True

    motion_proxy = MotionAnalysisProxy(session_id=session_id)
    session["motion_proxy"] = motion_proxy

    try:
        await motion_proxy.connect()
        while True:
            data = await websocket.receive_bytes()
            await motion_proxy.send_bytes(data)
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("VR frame socket error for session %s", session_id)
    finally:
        session["active_streams"]["frames"] = False
        await motion_proxy.close()
        _cleanup_session(session_id)
