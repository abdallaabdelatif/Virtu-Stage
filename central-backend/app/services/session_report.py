from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.api.schemas.sessions import (
    AnalysisComponentStatus,
    MotionAnalysisReport,
    ReportStatus,
    SessionReportResponse,
    SessionStatusResponse,
    TrainingSessionResponse,
    VoiceAnalysisReport,
)
from app.config import ANALYSIS_TIMEOUT_SECONDS


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def _component_timed_out(
    end_time: datetime | None, has_analysis: bool, now: datetime
) -> bool:
    if has_analysis or end_time is None:
        return False
    deadline = end_time + timedelta(seconds=ANALYSIS_TIMEOUT_SECONDS)
    if end_time.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
        end_time = end_time.replace(tzinfo=timezone.utc)
    return now >= deadline


def _component_status(
    has_analysis: bool,
    end_time: datetime | None,
    session_status: str,
    now: datetime,
) -> AnalysisComponentStatus:
    if has_analysis:
        return "ready"
    if session_status in {"failed", "cancelled"}:
        return "failed"
    if _component_timed_out(end_time, has_analysis, now):
        return "failed"
    if session_status in {"processing", "completed"} or end_time is not None:
        return "pending"
    return "pending"


def _report_status(
    voice_status: AnalysisComponentStatus,
    motion_status: AnalysisComponentStatus,
    session_status: str,
) -> ReportStatus:
    if voice_status == "ready" and motion_status == "ready":
        return "complete"
    if voice_status == "failed" and motion_status == "failed":
        return "failed"
    if (voice_status == "ready" and motion_status == "failed") or (
        voice_status == "failed" and motion_status == "ready"
    ):
        return "partial"
    if session_status in {"failed", "cancelled"}:
        return "failed"
    return "processing"


def map_training_session(data: dict) -> TrainingSessionResponse:
    return TrainingSessionResponse(
        session_id=str(data["session_id"]),
        user_id=str(data["user_id"]),
        scenario_type=data["scenario_type"],
        difficulty_level=data["difficulty_level"],
        status=data["status"],
        start_time=_parse_datetime(data.get("start_time")),
        end_time=_parse_datetime(data.get("end_time")),
        overall_score=data.get("overall_score"),
        voice_analysis_score=data.get("voice_analysis_score"),
        motion_analysis_score=data.get("motion_analysis_score"),
        created_at=_parse_datetime(data["created_at"]) or datetime.now(timezone.utc),
    )


def map_voice_analysis(data: dict) -> VoiceAnalysisReport:
    return VoiceAnalysisReport(
        anxiety_level=data["anxiety_level"],
        confidence_score=data["confidence_score"],
        clarity_level=data["clarity_level"],
        focus_score=data["focus_score"],
        pause_ratio=data["pause_ratio"],
        pause_count=data["pause_count"],
        longest_pause_seconds=data["longest_pause_seconds"],
        filler_words_count=data["filler_words_count"],
        speech_rate_wpm=data["speech_rate_wpm"],
        analyzed_at=_parse_datetime(data["analyzed_at"]) or datetime.now(timezone.utc),
    )


def map_motion_analysis(data: dict) -> MotionAnalysisReport:
    recommendations = data.get("recommendations")
    if isinstance(recommendations, str):
        recommendations = None
    return MotionAnalysisReport(
        head_stability_score=data["head_stability_score"],
        fidgeting_level=str(data["fidgeting_level"]),
        fidgeting_score=data["fidgeting_score"],
        hand_movement_score=data["hand_movement_score"],
        posture_quality=data["posture_quality"],
        posture_score=data["posture_score"],
        nervousness_indicator=data["nervousness_indicator"],
        motion_overall_score=data["motion_overall_score"],
        presentation_assessment=data.get("presentation_assessment"),
        recommendations=recommendations,
        dominant_posture_type=data.get("dominant_posture_type"),
        session_metrics=data.get("session_metrics"),
        analyzed_at=_parse_datetime(data["analyzed_at"]) or datetime.now(timezone.utc),
    )


def build_session_status(
    session: dict,
    voice: dict | None,
    motion: dict | None,
) -> SessionStatusResponse:
    return SessionStatusResponse(
        session_id=str(session["session_id"]),
        status=session["status"],
        voice_ready=voice is not None,
        motion_ready=motion is not None,
    )


def build_session_report(
    session: dict,
    voice: dict | None,
    motion: dict | None,
) -> SessionReportResponse:
    now = datetime.now(timezone.utc)
    end_time = _parse_datetime(session.get("end_time"))
    voice_status = _component_status(
        voice is not None, end_time, session["status"], now
    )
    motion_status = _component_status(
        motion is not None, end_time, session["status"], now
    )
    report_status = _report_status(voice_status, motion_status, session["status"])

    return SessionReportResponse(
        report_status=report_status,
        voice_status=voice_status,
        motion_status=motion_status,
        session=map_training_session(session),
        voice_analysis=map_voice_analysis(voice) if voice else None,
        motion_analysis=map_motion_analysis(motion) if motion else None,
    )
