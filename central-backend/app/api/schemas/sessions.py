from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


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
    confidence_level: float | None = None
    anxiety_level: float | None = None
    clarity_level: float | None = None
    focus_level: float | None = None
    voice_quality_score: float | None = None
    voice_quality_level: str | None = None
    fluency_score: float | None = None
    fluency_level: str | None = None
    energy_control_score: float | None = None
    energy_control_level: str | None = None
    articulation_score: float | None = None
    articulation_level: str | None = None
    words_per_minute: float | None = None
    pause_ratio: float | None = None
    filler_word_count: int | None = None
    pause_count: int | None = None
    longest_pause_sec: float | None = None
    confidence_feedback: str = ""
    anxiety_feedback: str = ""
    clarity_feedback: str = ""
    focus_feedback: str = ""
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
