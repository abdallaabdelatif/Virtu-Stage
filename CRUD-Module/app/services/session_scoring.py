from __future__ import annotations

import uuid
from statistics import mean

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.motion_analysis import MotionAnalysis
from app.models.session import SessionStatus, TrainingSession
from app.models.voice_analysis import VoiceAnalysis


def calculate_voice_score(
    confidence: float,
    clarity: float,
    focus: float,
    anxiety: float,
) -> float:
    return round(mean([confidence, clarity, focus, 1.0 - anxiety]) * 100, 2)


def calculate_overall_score(voice_score: float, motion_score: float) -> float:
    return round((voice_score + motion_score) / 2, 2)


async def apply_voice_score_to_session(
    db: AsyncSession,
    session: TrainingSession,
    voice_analysis: VoiceAnalysis,
) -> None:
    session.voice_analysis_score = calculate_voice_score(
        voice_analysis.confidence_score,
        voice_analysis.clarity_level,
        voice_analysis.focus_score,
        voice_analysis.anxiety_level,
    )


async def apply_motion_score_to_session(
    db: AsyncSession,
    session: TrainingSession,
    motion_score: float,
) -> None:
    session.motion_analysis_score = motion_score


async def try_complete_session(db: AsyncSession, session_id: uuid.UUID) -> TrainingSession | None:
    session = await db.get(TrainingSession, session_id)
    if session is None:
        return None

    voice = await db.scalar(
        select(VoiceAnalysis).where(VoiceAnalysis.session_id == session_id)
    )
    motion = await db.scalar(
        select(MotionAnalysis).where(MotionAnalysis.session_id == session_id)
    )
    if voice is None or motion is None:
        return session

    if session.voice_analysis_score is None:
        await apply_voice_score_to_session(db, session, voice)
    if session.motion_analysis_score is None:
        session.motion_analysis_score = motion.motion_overall_score

    session.overall_score = calculate_overall_score(
        session.voice_analysis_score or 0.0,
        session.motion_analysis_score or 0.0,
    )
    session.status = SessionStatus.completed
    return session
