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
    neutral: float
    happy: float
    sad: float
    angry: float
    anxiety_level: float
    confidence_score: float
    clarity_level: float
    focus_score: float
    pause_ratio: float
    pause_count: int
    longest_pause_sec: float
    filler_words_cnt: int
    speech_rate_wpm: float

    def to_model_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "emotions": {
                "neutral": self.neutral,
                "happy": self.happy,
                "sad": self.sad,
                "angry": self.angry,
            },
            "anxiety_level": self.anxiety_level,
            "confidence_score": self.confidence_score,
            "clarity_level": self.clarity_level,
            "focus_score": self.focus_score,
            "pause_ratio": self.pause_ratio,
            "pause_count": self.pause_count,
            "longest_pause_sec": self.longest_pause_sec,
            "filler_words_cnt": self.filler_words_cnt,
            "speech_rate_wpm": self.speech_rate_wpm,
        }


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
