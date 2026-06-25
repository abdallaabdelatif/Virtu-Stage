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


class ConversationalTTSMessage(BaseModel):
    type: str
    text: str | None = None
