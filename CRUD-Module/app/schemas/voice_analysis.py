import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VoiceAnalysisCreate(BaseModel):
    session_id: uuid.UUID
    anxiety_level: float = Field(ge=0.0, le=1.0)
    confidence_score: float = Field(ge=0.0, le=1.0)
    clarity_level: float = Field(ge=0.0, le=1.0)
    focus_score: float = Field(ge=0.0, le=1.0)
    pause_ratio: float
    pause_count: int
    longest_pause_sec: float
    filler_words_cnt: int
    speech_rate_wpm: float

    def to_model_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "anxiety_level": self.anxiety_level,
            "confidence_score": self.confidence_score,
            "clarity_level": self.clarity_level,
            "focus_score": self.focus_score,
            "pause_ratio": self.pause_ratio,
            "pause_count": self.pause_count,
            "longest_pause_seconds": self.longest_pause_sec,
            "filler_words_count": self.filler_words_cnt,
            "speech_rate_wpm": self.speech_rate_wpm,
        }


class VoiceAnalysisUpdate(BaseModel):
    anxiety_level: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    clarity_level: float | None = Field(default=None, ge=0.0, le=1.0)
    focus_score: float | None = Field(default=None, ge=0.0, le=1.0)
    pause_ratio: float | None = None
    pause_count: int | None = None
    longest_pause_seconds: float | None = None
    filler_words_count: int | None = None
    speech_rate_wpm: float | None = None


class VoiceAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    voice_analysis_id: uuid.UUID
    session_id: uuid.UUID
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
