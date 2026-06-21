# output schema for each part of voice analysis
# these parts are merged once all are ready


from __future__ import annotations
from pydantic import BaseModel


class EmotionScoresSchema(BaseModel):
    neutral: float
    happy: float
    sad: float
    angry: float
    dominant: str


class ParalinguisticScoresSchema(BaseModel):
    anxiety_level: float
    confidence_score: float
    clarity_level: float
    focus_score: float


class PauseAnalysisSchema(BaseModel):
    pause_ratio: float
    pause_count: int
    longest_pause_seconds: float


class AudioAnalysisResult(BaseModel):
    emotions: EmotionScoresSchema
    paralinguistic: ParalinguisticScoresSchema
    pauses: PauseAnalysisSchema
    duration_seconds: float


class TranscriptAnalysisResult(BaseModel):
    filler_word_count: int
    speech_rate_wpm: float


class VoiceAnalysisResult(BaseModel):
    session_id: str
    emotions: EmotionScoresSchema
    paralinguistic: ParalinguisticScoresSchema
    pauses: PauseAnalysisSchema
    filler_word_count: int
    speech_rate_wpm: float
