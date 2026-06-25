from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from app.models.motion_metrics import MotionMetrics
from app.models.presentation_ratings import PresentationAssessment


class PostureType(str, Enum):
    NEUTRAL = "neutral"
    EXCELLENT = "excellent"
    ACCEPTABLE = "acceptable"
    LEANING_FORWARD_WARNING = "leaning_forward_warning"
    LEANING_BACKWARD = "leaning_backward"
    SHOULDER_MISALIGNMENT = "shoulder_misalignment"
    HANDS_TOO_STATIC = "hands_too_static"
    BODY_TOO_STATIC = "body_too_static"
    HAND_NEAR_FACE = "hand_near_face"
    EXCESSIVE_HAND_MOVEMENT = "excessive_hand_movement"
    LOOKING_DOWN = "looking_down"
    CROSSED_ARMS = "crossed_arms"
    ONE_HAND_DOMINANT = "one_hand_dominant"
    FIDGETING = "fidgeting"


@dataclass
class MotionAnalysisResult:
    timestamp: datetime
    session_id: str
    metrics: MotionMetrics
    presentation: PresentationAssessment
    motion_overall_score: float
    recommendations: list[str] = field(default_factory=list)
    dominant_posture_type: str = PostureType.NEUTRAL.value

    def _session_metrics_dict(self) -> dict[str, Any]:
        return {
            "looking_down_ratio": round(self.metrics.looking_down_ratio, 3),
            "forward_lean_avg_deg": round(self.metrics.forward_lean_avg, 2),
            "backward_lean_avg_deg": round(self.metrics.backward_lean_avg, 2),
            "hand_near_face_ratio": round(self.metrics.hand_near_face_ratio, 3),
            "hand_tracking_ratio": round(self.metrics.hand_tracking_ratio, 3),
            "rocking_score": round(self.metrics.rocking_score, 3),
            "body_static_duration_sec": round(self.metrics.body_static_duration_sec, 1),
            "hand_dominance_ratio": round(self.metrics.hand_dominance_ratio, 3),
            "sudden_events": len(self.metrics.sudden_index),
            "repetitive_groups": len(self.metrics.repetitive_index),
        }

    def to_crud_payload(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "head_stability_score": round(self.metrics.head_stability_score, 2),
            "head_movement_variance": round(self.metrics.head_movement_variance, 4),
            "head_angle": round(self.metrics.max_rotation_head_degree, 4),
            "head_avg_velocity": round(self.metrics.head_avg_velocity, 4),
            "fidgeting_level": self.metrics.fidgeting_level,
            "fidgeting_score": round(self.metrics.fidgeting_score, 2),
            "sudden_index": self.metrics.sudden_index,
            "repetitive_index": self.metrics.repetitive_index,
            "hand_movement_score": round(self.metrics.hand_movement_score, 2),
            "left_hand_avg_velocity": round(self.metrics.left_hand_avg_velocity, 4),
            "right_hand_avg_velocity": round(self.metrics.right_hand_avg_velocity, 4),
            "posture_quality": round(self.metrics.posture_quality, 2),
            "posture_score": round(self.metrics.posture_score, 2),
            "nervousness_indicator": round(self.metrics.nervousness_indicator, 2),
            "motion_overall_score": round(self.motion_overall_score, 2),
            "presentation_assessment": self.presentation.to_dict(),
            "recommendations": self.recommendations,
            "dominant_posture_type": self.dominant_posture_type,
            "session_metrics": self._session_metrics_dict(),
        }

    def to_display_dict(self) -> dict[str, Any]:
        return {
            "analyzed_at": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "presentation_assessment": self.presentation.to_dict(),
            "dominant_posture_type": self.dominant_posture_type,
            "recommendations": self.recommendations,
            "rule_trigger_counts": self.metrics.rule_trigger_counts,
            "posture_type_counts": self.metrics.posture_type_counts,
            "session_metrics": self._session_metrics_dict(),
            "crud_numeric_scores": self.to_crud_payload(),
        }
