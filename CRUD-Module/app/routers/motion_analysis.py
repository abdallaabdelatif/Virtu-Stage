import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies.internal import require_internal_api_key
from app.models.motion_analysis import MotionAnalysis
from app.models.session import TrainingSession
from app.schemas.motion_analysis import (
    MotionAnalysisCreate,
    MotionAnalysisResponse,
    MotionAnalysisUpdate,
)
from app.services.session_scoring import apply_motion_score_to_session, try_complete_session

router = APIRouter(prefix="/motion-analysis", tags=["motion-analysis"])


@router.post(
    "", response_model=MotionAnalysisResponse, status_code=status.HTTP_201_CREATED
)
async def create_motion_analysis(
    payload: MotionAnalysisCreate,
    db: AsyncSession = Depends(get_session),
    _internal_access: None = Depends(require_internal_api_key),
) -> MotionAnalysis:
    existing = await db.scalar(
        select(MotionAnalysis).where(MotionAnalysis.session_id == payload.session_id)
    )
    if existing:
        return existing

    motion_analysis = MotionAnalysis(**payload.model_dump())
    db.add(motion_analysis)
    await db.flush()

    training_session = await db.get(TrainingSession, payload.session_id)
    if training_session is not None:
        await apply_motion_score_to_session(
            db, training_session, payload.motion_overall_score
        )
        await try_complete_session(db, payload.session_id)

    await db.commit()
    await db.refresh(motion_analysis)
    return motion_analysis


@router.get("/session/{session_id}", response_model=MotionAnalysisResponse)
async def get_motion_analysis_by_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    _internal_access: None = Depends(require_internal_api_key),
) -> MotionAnalysis:
    motion_analysis = await db.scalar(
        select(MotionAnalysis).where(MotionAnalysis.session_id == session_id)
    )
    if not motion_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Motion analysis not found for this session",
        )
    return motion_analysis


@router.get("/{motion_analysis_id}", response_model=MotionAnalysisResponse)
async def get_motion_analysis(
    motion_analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    _internal_access: None = Depends(require_internal_api_key),
) -> MotionAnalysis:
    motion_analysis = await db.get(MotionAnalysis, motion_analysis_id)
    if not motion_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Motion analysis not found",
        )
    return motion_analysis


@router.put("/{motion_analysis_id}", response_model=MotionAnalysisResponse)
async def update_motion_analysis(
    motion_analysis_id: uuid.UUID,
    payload: MotionAnalysisUpdate,
    db: AsyncSession = Depends(get_session),
    _internal_access: None = Depends(require_internal_api_key),
) -> MotionAnalysis:
    motion_analysis = await db.get(MotionAnalysis, motion_analysis_id)
    if not motion_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Motion analysis not found",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(motion_analysis, field, value)

    await db.commit()
    await db.refresh(motion_analysis)
    return motion_analysis


@router.delete("/{motion_analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_motion_analysis(
    motion_analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    _internal_access: None = Depends(require_internal_api_key),
) -> None:
    motion_analysis = await db.get(MotionAnalysis, motion_analysis_id)
    if not motion_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Motion analysis not found",
        )

    await db.delete(motion_analysis)
    await db.commit()
