import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies.internal import require_internal_api_key
from app.models.voice_analysis import VoiceAnalysis
from app.schemas.voice_analysis import (
    VoiceAnalysisCreate,
    VoiceAnalysisResponse,
    VoiceAnalysisUpdate,
)
from app.services.session_scoring import (
    apply_voice_score_to_session,
    try_complete_session,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice-analysis", tags=["voice-analysis"])


@router.post(
    "", response_model=VoiceAnalysisResponse, status_code=status.HTTP_201_CREATED
)
async def create_voice_analysis(
    payload: VoiceAnalysisCreate,
    db: AsyncSession = Depends(get_session),
    _internal_access: None = Depends(require_internal_api_key),
) -> VoiceAnalysis:
    existing = await db.scalar(
        select(VoiceAnalysis).where(VoiceAnalysis.session_id == payload.session_id)
    )
    if existing:
        return existing

    voice_analysis = VoiceAnalysis(**payload.to_model_dict())
    db.add(voice_analysis)
    await db.flush()

    from app.models.session import TrainingSession

    training_session = await db.get(TrainingSession, payload.session_id)
    if training_session is not None:
        await apply_voice_score_to_session(db, training_session, voice_analysis)
        await try_complete_session(db, payload.session_id)

    await db.commit()
    await db.refresh(voice_analysis)
    return voice_analysis


@router.get("/session/{session_id}", response_model=VoiceAnalysisResponse)
async def get_voice_analysis_by_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    _internal_access: None = Depends(require_internal_api_key),
) -> VoiceAnalysis:
    voice_analysis = await db.scalar(
        select(VoiceAnalysis).where(VoiceAnalysis.session_id == session_id)
    )
    if not voice_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Voice analysis not found"
        )
    return voice_analysis


@router.get("/{voice_analysis_id}", response_model=VoiceAnalysisResponse)
async def get_voice_analysis(
    voice_analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    _internal_access: None = Depends(require_internal_api_key),
) -> VoiceAnalysis:
    voice_analysis = await db.get(VoiceAnalysis, voice_analysis_id)
    if not voice_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Voice analysis not found"
        )
    return voice_analysis


@router.put("/{voice_analysis_id}", response_model=VoiceAnalysisResponse)
async def update_voice_analysis(
    voice_analysis_id: uuid.UUID,
    payload: VoiceAnalysisUpdate,
    db: AsyncSession = Depends(get_session),
    _internal_access: None = Depends(require_internal_api_key),
) -> VoiceAnalysis:
    voice_analysis = await db.get(VoiceAnalysis, voice_analysis_id)
    if not voice_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Voice analysis not found"
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(voice_analysis, field, value)

    await db.commit()
    await db.refresh(voice_analysis)
    return voice_analysis


@router.delete("/{voice_analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_voice_analysis(
    voice_analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    _internal_access: None = Depends(require_internal_api_key),
) -> None:
    voice_analysis = await db.get(VoiceAnalysis, voice_analysis_id)
    if not voice_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Voice analysis not found"
        )

    await db.delete(voice_analysis)
    await db.commit()
