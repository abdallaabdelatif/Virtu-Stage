import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.session import DifficultyLevel, ScenarioType, SessionStatus


class TrainingSessionCreate(BaseModel):
    user_id: uuid.UUID
    scenario_type: ScenarioType
    difficulty_level: DifficultyLevel
    session_id: uuid.UUID | None = None


class TrainingSessionUpdate(BaseModel):
    status: Optional[SessionStatus] = None
    difficulty_level: Optional[DifficultyLevel] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    overall_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    voice_analysis_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    motion_analysis_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)

    @model_validator(mode="after")
    def validate_end_after_start(self) -> "TrainingSessionUpdate":
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValueError("end_time must be after start_time")
        return self


class TrainingSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: uuid.UUID
    user_id: uuid.UUID
    scenario_type: ScenarioType
    difficulty_level: DifficultyLevel
    status: SessionStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    overall_score: Optional[float] = None
    voice_analysis_score: Optional[float] = None
    motion_analysis_score: Optional[float] = None
    created_at: datetime
