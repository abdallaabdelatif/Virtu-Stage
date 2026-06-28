from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas.sessions import (
    SessionReportResponse,
    SessionStatusResponse,
    TrainingSessionResponse,
)
from app.auth.deps import get_current_active_user, require_admin
from app.clients.crud_client import crud_client
from app.services.session_report import (
    build_session_report,
    build_session_status,
    map_training_session,
)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _is_admin(user: dict) -> bool:
    return user.get("role") == "admin"


async def _get_owned_session(session_id: str, user: dict) -> dict:
    try:
        session = await crud_client.get_training_session(session_id)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="CRUD service is unavailable",
        ) from exc

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    if not _is_admin(user) and str(session["user_id"]) != str(user["user_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this session",
        )
    return session


@router.get("/me", response_model=list[TrainingSessionResponse])
async def list_my_sessions(user=Depends(get_current_active_user)):
    try:
        sessions = await crud_client.list_training_sessions_by_user(
            str(user["user_id"])
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="CRUD service is unavailable",
        ) from exc
    return [map_training_session(session) for session in sessions]


@router.get("/{session_id}", response_model=TrainingSessionResponse)
async def get_session_detail(session_id: str, user=Depends(get_current_active_user)):
    session = await _get_owned_session(session_id, user)
    return map_training_session(session)


@router.get("/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(session_id: str, user=Depends(get_current_active_user)):
    session = await _get_owned_session(session_id, user)
    try:
        voice = await crud_client.get_voice_analysis_by_session(session_id)
        motion = await crud_client.get_motion_analysis_by_session(session_id)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="CRUD service is unavailable",
        ) from exc
    return build_session_status(session, voice, motion)


@router.get("/{session_id}/report", response_model=SessionReportResponse)
async def get_session_report(session_id: str, user=Depends(get_current_active_user)):
    session = await _get_owned_session(session_id, user)
    try:
        voice = await crud_client.get_voice_analysis_by_session(session_id)
        motion = await crud_client.get_motion_analysis_by_session(session_id)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="CRUD service is unavailable",
        ) from exc
    return build_session_report(session, voice, motion)
