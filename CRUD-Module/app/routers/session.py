import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies.internal import require_internal_api_key
from app.models.session import SessionStatus, TrainingSession
from app.schemas.session import (
    TrainingSessionCreate,
    TrainingSessionResponse,
    TrainingSessionUpdate,
)

router = APIRouter(prefix="/sessions", tags=["training-sessions"])


@router.post(
    "", response_model=TrainingSessionResponse, status_code=status.HTTP_201_CREATED
)
async def create_session(
    payload: TrainingSessionCreate,
    session: AsyncSession = Depends(get_session),
    _internal_access: None = Depends(require_internal_api_key),
) -> TrainingSession:
    data = payload.model_dump()
    session_id = data.pop("session_id", None)
    if session_id is not None:
        training_session = TrainingSession(session_id=session_id, **data)
    else:
        training_session = TrainingSession(**data)

    training_session.status = SessionStatus.in_progress
    if training_session.start_time is None:
        training_session.start_time = datetime.now(timezone.utc)

    session.add(training_session)
    await session.commit()
    await session.refresh(training_session)
    return training_session


@router.get("/user/{user_id}", response_model=list[TrainingSessionResponse])
async def list_sessions_by_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    _internal_access: None = Depends(require_internal_api_key),
) -> list[TrainingSession]:
    result = await db.execute(
        select(TrainingSession)
        .where(TrainingSession.user_id == user_id)
        .order_by(TrainingSession.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/user/{user_id}/paginated", response_model=list[TrainingSessionResponse])
async def list_sessions_by_user_paginated(
    user_id: uuid.UUID,
    skip: int = Query(default=0, ge=0, description="Records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Max records to return"),
    db: AsyncSession = Depends(get_session),
    _internal_access: None = Depends(require_internal_api_key),
) -> list[TrainingSession]:
    result = await db.execute(
        select(TrainingSession)
        .where(TrainingSession.user_id == user_id)
        .order_by(TrainingSession.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


@router.post("/{session_id}/finish", response_model=TrainingSessionResponse)
async def finish_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    _internal_access: None = Depends(require_internal_api_key),
) -> TrainingSession:
    training_session = await db.get(TrainingSession, session_id)
    if not training_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    if training_session.status in {
        SessionStatus.completed,
        SessionStatus.failed,
        SessionStatus.cancelled,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session is already in a terminal state",
        )

    now = datetime.now(timezone.utc)
    training_session.end_time = now
    training_session.status = SessionStatus.processing
    await db.commit()
    await db.refresh(training_session)
    return training_session


@router.get("/{session_id}", response_model=TrainingSessionResponse)
async def get_session_by_id(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    _internal_access: None = Depends(require_internal_api_key),
) -> TrainingSession:
    training_session = await db.get(TrainingSession, session_id)
    if not training_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    return training_session


@router.put("/{session_id}", response_model=TrainingSessionResponse)
async def update_session(
    session_id: uuid.UUID,
    payload: TrainingSessionUpdate,
    db: AsyncSession = Depends(get_session),
    _internal_access: None = Depends(require_internal_api_key),
) -> TrainingSession:
    training_session = await db.get(TrainingSession, session_id)
    if not training_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(training_session, field, value)

    await db.commit()
    await db.refresh(training_session)
    return training_session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    _internal_access: None = Depends(require_internal_api_key),
) -> None:
    training_session = await db.get(TrainingSession, session_id)
    if not training_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    await db.delete(training_session)
    await db.commit()
