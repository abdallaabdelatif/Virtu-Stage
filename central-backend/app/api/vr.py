from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import secrets

import websockets
from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect, HTTPException, Header, status
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
from app.config import INTERNAL_API_KEY, VOICE_ANALYSIS_WS_URL
from app.auth.jwt import verify_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["vr"])

session_store: dict[str, dict] = {}


async def require_internal_api_key(
    x_internal_api_key: str | None = Header(default=None),
) -> None:
    if not x_internal_api_key or not secrets.compare_digest(
        x_internal_api_key, INTERNAL_API_KEY
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal service credentials",
        )


async def authenticate_vr_websocket(websocket: WebSocket) -> dict | None:
    authorization = websocket.headers.get("authorization", "")
    if not authorization.lower().startswith("bearer "):
        await websocket.close(code=1008, reason="Not authenticated")
        return None
    try:
        payload = verify_token(authorization.split(" ", 1)[1])
        user = await crud_client.get_user(payload.get("sub", ""))
        if not user or not user.get("is_active", False):
            raise ValueError("Inactive or missing user")
        return user
    except Exception:
        await websocket.close(code=1008, reason="Invalid authentication credentials")
        return None


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
async def create_session(request: Request, payload: VRSessionCreate):
    session_id = payload.session_id
    if session_id in session_store:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Session already exists"
        )

    authenticated_user = request.state.user
    user_id = str(authenticated_user["user_id"])
    session_store[session_id] = {
        "mode": payload.mode,
        "job": payload.job,
        "user_id": user_id,
        "voice_proxy": None,
        "conv_proxy": None,
        "motion_proxy": None,
    }

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
        session_store.pop(session_id, None)
        logger.exception(
            "Could not create CRUD training session for VR session %s", session_id
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not create persisted session",
        )

    return {"session_id": session_id}


@router.post("/sessions/{session_id}/finish", status_code=status.HTTP_200_OK)
async def finish_session(request: Request, session_id: str):
    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    if session.get("user_id") != str(request.state.user["user_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Session access denied"
        )
    try:
        stored = await crud_client.finish_training_session(session_id)
    except Exception:
        logger.exception("Could not finish CRUD training session %s", session_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not finish session",
        )
    return stored


@router.post(
    "/voice-analyses",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_internal_api_key)],
)
async def ingest_voice_analysis(payload: VoiceAnalysisResultPayload):
    logger.info("received voice analysis payload: %s", payload.model_dump())
    try:
        stored = await crud_client.create_voice_analysis(payload.to_model_dict())
    except Exception:
        logger.exception("Failed to store voice analysis for session %s", payload.session_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not store voice analysis",
        )
    logger.info("voice analysis stored successfully: %s", stored)
    return stored


@router.post(
    "/motion-analyses",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_internal_api_key)],
)
async def ingest_motion_analysis(payload: MotionAnalysisResultPayload):
    try:
        stored = await crud_client.create_motion_analysis(payload.model_dump())
    except Exception:
        logger.exception(
            "Failed to store motion analysis for session %s", payload.session_id
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not store motion analysis",
        )
    return stored


@router.websocket("/ws/internal/voice-analysis/transcript/{session_id}")
async def forward_transcript_to_voice(websocket: WebSocket, session_id: str):
    supplied_key = websocket.headers.get("x-internal-api-key", "")
    if not secrets.compare_digest(supplied_key, INTERNAL_API_KEY):
        await websocket.close(code=1008, reason="Invalid internal service credentials")
        return

    upstream = None
    try:
        upstream_url = (
            f"{VOICE_ANALYSIS_WS_URL.rstrip('/')}"
            f"/ws/voice-analysis/transcript/{session_id}"
        )
        upstream = await websockets.connect(upstream_url)
        await websocket.accept()
        while True:
            await upstream.send(await websocket.receive_text())
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("Transcript proxy failed for session %s", session_id)
        if websocket.client_state.name == "CONNECTED":
            await websocket.close(code=1011)
    finally:
        if upstream is not None:
            await upstream.close()


@router.websocket("/ws/vr/audio/{session_id}")
async def vr_audio_socket(websocket: WebSocket, session_id: str):
    user = await authenticate_vr_websocket(websocket)
    if user is None:
        return

    session = session_store.get(session_id)
    if session is None or session.get("user_id") != str(user["user_id"]):
        await websocket.close(code=1008)
        return
    await websocket.accept()

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
    user = await authenticate_vr_websocket(websocket)
    if user is None:
        return
    session = session_store.get(session_id)
    if session is None or session.get("user_id") != str(user["user_id"]):
        await websocket.close(code=1008)
        return
    await websocket.accept()

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
