import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.voice_analysis import VoiceAnalysis
from app.schemas.voice_analysis import (
    VoiceAnalysisCreate,
    VoiceAnalysisResponse,
    VoiceAnalysisUpdate,
)

router = APIRouter(prefix="/voice-analysis", tags=["voice-analysis"])


@router.post(
    "", response_model=VoiceAnalysisResponse, status_code=status.HTTP_201_CREATED
)
async def create_voice_analysis(
    payload: VoiceAnalysisCreate,
    db: AsyncSession = Depends(get_session),
) -> VoiceAnalysis:
    existing = await db.scalar(
        select(VoiceAnalysis).where(VoiceAnalysis.session_id == payload.session_id)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Voice analysis already exists for this session",
        )

    voice_analysis = VoiceAnalysis(**payload.to_model_dict())
    db.add(voice_analysis)
    await db.commit()
    await db.refresh(voice_analysis)
    return voice_analysis


@router.get("/{voice_analysis_id}", response_model=VoiceAnalysisResponse)
async def get_voice_analysis(
    voice_analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> VoiceAnalysis:
    voice_analysis = await db.get(VoiceAnalysis, voice_analysis_id)
    if not voice_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Voice analysis not found"
        )
    return voice_analysis


@router.get("/session/{session_id}", response_model=VoiceAnalysisResponse)
async def get_voice_analysis_by_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> VoiceAnalysis:
    voice_analysis = await db.scalar(
        select(VoiceAnalysis).where(VoiceAnalysis.session_id == session_id)
    )
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
) -> VoiceAnalysis:
    voice_analysis = await db.get(VoiceAnalysis, voice_analysis_id)
    if not voice_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Voice analysis not found"
        )

    if payload.emotions is not None:
        voice_analysis.emotion_neutral = payload.emotions.neutral
        voice_analysis.emotion_happy = payload.emotions.happy
        voice_analysis.emotion_sad = payload.emotions.sad
        voice_analysis.emotion_angry = payload.emotions.angry
        voice_analysis.pause_ratio = payload.pause_ratio
        voice_analysis.pause_count = payload.pause_count
        voice_analysis.longest_pause_seconds = payload.longest_pause_seconds
        voice_analysis.filler_words_count = payload.filler_words_count
        voice_analysis.speech_rate_wpm = payload.speech_rate_wpm

        scores = {
            "neutral": payload.emotions.neutral,
            "happy": payload.emotions.happy,
            "sad": payload.emotions.sad,
            "angry": payload.emotions.angry,
        }
        voice_analysis.dominant_emotion = max(scores, key=scores.get)

    for field in ("anxiety_level", "confidence_score", "clarity_level", "focus_score"):
        value = getattr(payload, field)
        if value is not None:
            setattr(voice_analysis, field, value)
    await db.commit()
    await db.refresh(voice_analysis)
    return voice_analysis


@router.delete("/{voice_analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_voice_analysis(
    voice_analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> None:
    voice_analysis = await db.get(VoiceAnalysis, voice_analysis_id)
    if not voice_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Voice analysis not found"
        )

    await db.delete(voice_analysis)
    await db.commit()
