from __future__ import annotations
import uuid
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
    emotions: dict
    anxiety_level: float
    confidence_score: float
    clarity_level: float
    focus_score: float


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
