from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MotionMetrics:
    """Notebook of calculated values for one session."""

    max_rotation_head_degree: float = 0.0
    head_movement_variance: float = 0.0
    head_avg_velocity: float = 0.0
    head_stability_score: float = 0.0
    head_pitch_avg: float = 0.0
    forward_lean_avg: float = 0.0
    looking_down_ratio: float = 0.0

    shoulder_alignment_diff_cm: float = 0.0
    posture_quality: float = 0.0
    posture_score: float = 0.0

    left_hand_avg_velocity: float = 0.0
    right_hand_avg_velocity: float = 0.0
    hand_movement_score: float = 0.0
    left_hand_total_movement_m: float = 0.0
    right_hand_total_movement_m: float = 0.0
    hands_static_duration_sec: float = 0.0
    hand_dominance_ratio: float = 0.5

    sudden_index: list[dict[str, Any]] = field(default_factory=list)
    repetitive_index: list[dict[str, Any]] = field(default_factory=list)

    fidgeting_score: float = 0.0
    fidgeting_level: str = "low"
    nervousness_indicator: float = 0.0
    motion_overall_score: float = 0.0

    hand_near_face_ratio: float = 0.0
    hand_tracking_ratio: float = 0.0
    backward_lean_avg: float = 0.0
    rocking_score: float = 0.0
    body_static_duration_sec: float = 0.0

    # Categorical assessment (primary output)
    presentation_overall: str = "developing"
    posture_rating: str = "developing"
    gaze_rating: str = "developing"
    gesture_rating: str = "developing"
    composure_rating: str = "developing"
    stability_rating: str = "developing"

    rule_trigger_counts: dict[str, int] = field(default_factory=dict)
    posture_type_counts: dict[str, int] = field(default_factory=dict)
