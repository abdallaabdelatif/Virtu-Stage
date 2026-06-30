from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class VRSessionCreate(BaseModel):
    session_id: str = Field(..., description="Unique VR session identifier")
    mode: int = Field(..., ge=1, le=2, description="Conversation mode")
    job: str | None = Field(None, description="Job name or prompt target")
    user_id: str | None = Field(None, description="Associated user id")


class VRAudioControlMessage(BaseModel):
    type: str
    mode: int | None = None
    job: str | None = None
    audio_start: bool | None = None
    audio_end: bool | None = None


class VRFrameBatch(BaseModel):
    session_id: str
    batch_index: int
    frame_count: int
    timestamp_ms: int


class VoiceAnalysisResultPayload(BaseModel):
    session_id: str
    confidence_level: float | None = None
    anxiety_level: float | None = None
    clarity_level: float | None = None
    focus_level: float | None = None
    confidence_reasons: list[str] = Field(default_factory=list)
    anxiety_reasons: list[str] = Field(default_factory=list)
    clarity_reasons: list[str] = Field(default_factory=list)
    focus_reasons: list[str] = Field(default_factory=list)
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

    def to_model_dict(self) -> dict[str, Any]:
        return self.model_dump()


class MotionAnalysisResultPayload(BaseModel):
    session_id: str
    head_stability_score: float = Field(ge=0.0)
    head_movement_variance: float = Field(ge=0.0)
    head_angle: float
    head_avg_velocity: float = Field(ge=0.0)
    fidgeting_level: str
    fidgeting_score: float = Field(ge=0.0)
    sudden_index: dict | list | None = None
    repetitive_index: dict | list | None = None
    hand_movement_score: float = Field(ge=0.0)
    left_hand_avg_velocity: float = Field(ge=0.0)
    right_hand_avg_velocity: float = Field(ge=0.0)
    posture_quality: float = Field(ge=0.0)
    posture_score: float = Field(ge=0.0)
    nervousness_indicator: float = Field(ge=0.0)
    motion_overall_score: float = Field(ge=0.0)
    presentation_assessment: dict | None = None
    recommendations: list[str] | None = None
    dominant_posture_type: str | None = None
    session_metrics: dict | None = None


class ConversationalTTSMessage(BaseModel):
    type: str
    text: str | None = None
