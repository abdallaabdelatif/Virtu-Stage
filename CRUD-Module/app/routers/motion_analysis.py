import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.models.motion_analysis import MotionAnalysis
from app.models.session import TrainingSession
from app.schemas.motion_analysis import (
    MotionAnalysisCreate,
    MotionAnalysisResponse,
    MotionAnalysisUpdate,
)

router = APIRouter(prefix="/motion-analysis", tags=["motion-analysis"])


@router.post(
    "", response_model=MotionAnalysisResponse, status_code=status.HTTP_201_CREATED
)
async def create_motion_analysis(
    payload: MotionAnalysisCreate,
    db: AsyncSession = Depends(get_session),
) -> MotionAnalysis:
    existing = await db.scalar(
        select(MotionAnalysis).where(MotionAnalysis.session_id == payload.session_id)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Motion analysis already exists for this session",
        )

    motion_analysis = MotionAnalysis(**payload.model_dump())
    db.add(motion_analysis)

    training_session = await db.get(TrainingSession, payload.session_id)
    if training_session is not None:
        training_session.motion_analysis_score = payload.motion_overall_score

    await db.commit()
    await db.refresh(motion_analysis)
    return motion_analysis


@router.get("/{motion_analysis_id}", response_model=MotionAnalysisResponse)
async def get_motion_analysis(
    motion_analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> MotionAnalysis:
    motion_analysis = await db.get(MotionAnalysis, motion_analysis_id)
    if not motion_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Motion analysis not found",
        )
    return motion_analysis


@router.get("/session/{session_id}", response_model=MotionAnalysisResponse)
async def get_motion_analysis_by_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
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


@router.put("/{motion_analysis_id}", response_model=MotionAnalysisResponse)
async def update_motion_analysis(
    motion_analysis_id: uuid.UUID,
    payload: MotionAnalysisUpdate,
    db: AsyncSession = Depends(get_session),
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
) -> None:
    motion_analysis = await db.get(MotionAnalysis, motion_analysis_id)
    if not motion_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Motion analysis not found",
        )

    await db.delete(motion_analysis)
    await db.commit()
