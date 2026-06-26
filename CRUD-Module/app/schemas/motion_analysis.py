import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from app.models.motion_analysis import FidgetingLevel


class MotionAnalysisCreate(BaseModel):
    session_id: uuid.UUID
    head_stability_score: float = Field(ge=0.0)
    head_movement_variance: float = Field(ge=0.0)
    head_angle: float
    head_avg_velocity: float = Field(ge=0.0)
    fidgeting_level: FidgetingLevel
    fidgeting_score: float = Field(ge=0.0)
    sudden_index: Any = None
    repetitive_index: Any = None
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


class MotionAnalysisUpdate(BaseModel):
    head_stability_score: float | None = Field(default=None, ge=0.0)
    head_movement_variance: float | None = Field(default=None, ge=0.0)
    head_angle: float | None = None
    head_avg_velocity: float | None = Field(default=None, ge=0.0)
    fidgeting_level: FidgetingLevel | None = None
    fidgeting_score: float | None = Field(default=None, ge=0.0)
    sudden_index: Any = None
    repetitive_index: Any = None
    hand_movement_score: float | None = Field(default=None, ge=0.0)
    left_hand_avg_velocity: float | None = Field(default=None, ge=0.0)
    right_hand_avg_velocity: float | None = Field(default=None, ge=0.0)
    posture_quality: float | None = Field(default=None, ge=0.0)
    posture_score: float | None = Field(default=None, ge=0.0)
    nervousness_indicator: float | None = Field(default=None, ge=0.0)
    motion_overall_score: float | None = Field(default=None, ge=0.0)
    presentation_assessment: dict | None = None
    recommendations: list[str] | None = None
    dominant_posture_type: str | None = None
    session_metrics: dict | None = None


class MotionAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    motion_analysis_id: uuid.UUID
    session_id: uuid.UUID
    head_stability_score: float
    head_movement_variance: float
    head_angle: float
    head_avg_velocity: float
    fidgeting_level: FidgetingLevel
    fidgeting_score: float
    sudden_index: Any
    repetitive_index: Any
    hand_movement_score: float
    left_hand_avg_velocity: float
    right_hand_avg_velocity: float
    posture_quality: float
    posture_score: float
    nervousness_indicator: float
    motion_overall_score: float
    presentation_assessment: Any
    recommendations: Any
    dominant_posture_type: str | None
    session_metrics: Any
    analyzed_at: datetime
