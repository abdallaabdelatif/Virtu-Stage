from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TrainingSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    user_id: str
    scenario_type: Literal["interview", "public_speaking"]
    difficulty_level: Literal["easy", "medium", "hard"]
    status: Literal[
        "pending",
        "in_progress",
        "processing",
        "completed",
        "failed",
        "cancelled",
    ]
    start_time: datetime | None = None
    end_time: datetime | None = None
    overall_score: float | None = None
    voice_analysis_score: float | None = None
    motion_analysis_score: float | None = None
    created_at: datetime


class SessionStatusResponse(BaseModel):
    session_id: str
    status: Literal[
        "pending",
        "in_progress",
        "processing",
        "completed",
        "failed",
        "cancelled",
    ]
    voice_ready: bool
    motion_ready: bool


AnalysisComponentStatus = Literal["pending", "ready", "failed"]
ReportStatus = Literal["processing", "complete", "partial", "failed"]


class VoiceAnalysisReport(BaseModel):
    anxiety_level: float
    confidence_score: float
    clarity_level: float
    focus_score: float
    pause_ratio: float
    pause_count: int
    longest_pause_seconds: float
    filler_words_count: int
    speech_rate_wpm: float
    analyzed_at: datetime


class MotionAnalysisReport(BaseModel):
    head_stability_score: float
    fidgeting_level: str
    fidgeting_score: float
    hand_movement_score: float
    posture_quality: float
    posture_score: float
    nervousness_indicator: float
    motion_overall_score: float
    presentation_assessment: dict | None = None
    recommendations: list[str] | None = None
    dominant_posture_type: str | None = None
    session_metrics: dict | None = None
    analyzed_at: datetime


class SessionReportResponse(BaseModel):
    report_status: ReportStatus
    voice_status: AnalysisComponentStatus
    motion_status: AnalysisComponentStatus
    session: TrainingSessionResponse
    voice_analysis: VoiceAnalysisReport | None = None
    motion_analysis: MotionAnalysisReport | None = None
