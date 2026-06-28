import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class VoiceAnalysisBase(BaseModel):
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


class VoiceAnalysisCreate(VoiceAnalysisBase):
    session_id: uuid.UUID

    def to_model_dict(self) -> dict[str, Any]:
        return self.model_dump()


class VoiceAnalysisUpdate(VoiceAnalysisBase):
    pass


class VoiceAnalysisResponse(VoiceAnalysisBase):
    model_config = ConfigDict(from_attributes=True)

    voice_analysis_id: uuid.UUID
    session_id: uuid.UUID
    analyzed_at: datetime
