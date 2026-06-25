import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.voice_analysis import DominantEmotion


class EmotionScores(BaseModel):
    neutral: float = Field(ge=0.0, le=1.0)
    happy: float = Field(ge=0.0, le=1.0)
    sad: float = Field(ge=0.0, le=1.0)
    angry: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def probabilities_sum_to_one(self) -> "EmotionScores":
        total = self.neutral + self.happy + self.sad + self.angry
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Emotion probabilities must sum to 1.0, got {total:.4f}")
        return self


class VoiceAnalysisCreate(BaseModel):
    session_id: uuid.UUID
    emotions: EmotionScores
    anxiety_level: float = Field(ge=0.0, le=1.0)
    confidence_score: float = Field(ge=0.0, le=1.0)
    clarity_level: float = Field(ge=0.0, le=1.0)
    focus_score: float = Field(ge=0.0, le=1.0)
    pause_ratio: float
    pause_count: int
    longest_pause_sec: float
    filler_words_cnt: int
    speech_rate_wpm: float

    @model_validator(mode="after")
    def derive_dominant_emotion(self) -> "VoiceAnalysisCreate":
        scores = {
            "neutral": self.emotions.neutral,
            "happy": self.emotions.happy,
            "sad": self.emotions.sad,
            "angry": self.emotions.angry,
        }
        self._dominant = max(scores, key=scores.get)
        return self

    def to_model_dict(self) -> dict:  # used to match the model structure
        return {
            "session_id": self.session_id,
            "emotion_neutral": self.emotions.neutral,
            "emotion_happy": self.emotions.happy,
            "emotion_sad": self.emotions.sad,
            "emotion_angry": self.emotions.angry,
            "dominant_emotion": self._dominant,
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
    emotions: EmotionScores | None = None
    anxiety_level: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    clarity_level: float | None = Field(default=None, ge=0.0, le=1.0)
    focus_score: float | None = Field(default=None, ge=0.0, le=1.0)
    pause_ratio: float | None
    pause_count: int | None
    longest_pause_seconds: float | None
    filler_words_count: int | None
    speech_rate_wpm: float | None


class VoiceAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    voice_analysis_id: uuid.UUID
    session_id: uuid.UUID
    emotion_neutral: float
    emotion_happy: float
    emotion_sad: float
    emotion_angry: float
    dominant_emotion: DominantEmotion
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
