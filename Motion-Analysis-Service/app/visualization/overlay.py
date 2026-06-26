from __future__ import annotations

import cv2
import numpy as np

from app.models.hand_data import HAND_CONNECTIONS
from app.models.motion_analysis_result import PostureType
from app.models.motion_analysis_service import FrameEvaluation
from app.models.motion_rule_engine import RuleSeverity
from app.models.motion_frame_data import (
    LEFT_ELBOW,
    LEFT_HIP,
    LEFT_SHOULDER,
    LEFT_WRIST,
    NOSE,
    RIGHT_ELBOW,
    RIGHT_HIP,
    RIGHT_SHOULDER,
    RIGHT_WRIST,
    Landmark2D,
    MotionFrameData,
)

SEVERITY_COLORS = {
    RuleSeverity.EXCELLENT: (0, 200, 0),
    RuleSeverity.ACCEPTABLE: (0, 200, 200),
    RuleSeverity.WARNING: (0, 140, 255),
    RuleSeverity.POOR: (0, 0, 255),
    RuleSeverity.INFO: (255, 180, 0),
}

POSTURE_COLORS = {
    PostureType.EXCELLENT: (0, 200, 0),
    PostureType.ACCEPTABLE: (0, 200, 200),
    PostureType.NEUTRAL: (200, 200, 200),
    PostureType.LEANING_FORWARD_WARNING: (0, 140, 255),
    PostureType.LEANING_BACKWARD: (0, 100, 255),
    PostureType.SHOULDER_MISALIGNMENT: (0, 100, 255),
    PostureType.HANDS_TOO_STATIC: (255, 180, 0),
    PostureType.BODY_TOO_STATIC: (255, 150, 0),
    PostureType.HAND_NEAR_FACE: (200, 0, 200),
    PostureType.EXCESSIVE_HAND_MOVEMENT: (0, 0, 255),
    PostureType.LOOKING_DOWN: (180, 0, 255),
    PostureType.CROSSED_ARMS: (0, 0, 220),
    PostureType.ONE_HAND_DOMINANT: (255, 120, 0),
    PostureType.FIDGETING: (0, 80, 255),
}


def draw_skeleton(frame: np.ndarray, motion_frame: MotionFrameData) -> None:
    h, w, _ = frame.shape

    def pt(lm: Landmark2D) -> tuple[int, int]:
        return int(lm.x * w), int(lm.y * h)

    mid_shoulder = motion_frame.mid_shoulder
    mid_hip = motion_frame.mid_hip

    connections = [
        (motion_frame.nose, mid_shoulder, "head"),
        (motion_frame.left_shoulder, motion_frame.left_elbow, "arm"),
        (motion_frame.left_elbow, motion_frame.left_wrist, "arm"),
        (motion_frame.right_shoulder, motion_frame.right_elbow, "arm"),
        (motion_frame.right_elbow, motion_frame.right_wrist, "arm"),
        (motion_frame.left_shoulder, motion_frame.right_shoulder, "shoulder"),
        (mid_shoulder, mid_hip, "spine"),
    ]

    for a, b, kind in connections:
        a_pt = pt(a)
        b_pt = pt(b)
        color = (255, 0, 0) if kind == "arm" else (0, 255, 255) if kind == "spine" else (0, 0, 255)
        cv2.line(frame, a_pt, b_pt, color, 2)
        cv2.circle(frame, a_pt, 4, color, -1)

    for lm in (
        motion_frame.left_wrist,
        motion_frame.right_wrist,
        motion_frame.nose,
    ):
        cv2.circle(frame, pt(lm), 5, (0, 255, 0), -1)

    draw_hands(frame, motion_frame)


def draw_hands(frame: np.ndarray, motion_frame: MotionFrameData) -> None:
    h, w, _ = frame.shape

    def pt(lm: Landmark2D) -> tuple[int, int]:
        return int(lm.x * w), int(lm.y * h)

    for hand in (motion_frame.left_hand, motion_frame.right_hand):
        if hand is None or not hand.is_tracked:
            continue
        color = (255, 128, 0)
        for a, b in HAND_CONNECTIONS:
            cv2.line(frame, pt(hand.landmarks[a]), pt(hand.landmarks[b]), color, 2)
        for tip in hand.fingertips:
            cv2.circle(frame, pt(tip), 4, (0, 255, 255), -1)
        cv2.circle(frame, pt(hand.palm_center), 5, (255, 0, 255), -1)


def draw_overlay(
    frame: np.ndarray,
    evaluation: FrameEvaluation,
    frame_count: int,
    session_seconds: float,
) -> None:
    h, w, _ = frame.shape
    overlay = frame.copy()
    cv2.rectangle(overlay, (10, 10), (w - 10, min(h - 10, 320)), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)

    posture_color = POSTURE_COLORS.get(evaluation.posture_type, (200, 200, 200))
    y = 35
    cv2.putText(
        frame,
        f"Posture: {evaluation.posture_type.value.replace('_', ' ').title()}",
        (20, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        posture_color,
        2,
    )
    y += 28
    cv2.putText(
        frame,
        f"Frame {frame_count} | {session_seconds:.1f}s | "
        f"Lean {evaluation.forward_lean_deg:.1f} | Pitch {evaluation.head_pitch_deg:.1f}",
        (20, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (220, 220, 220),
        1,
    )
    y += 24
    cv2.putText(
        frame,
        f"L hand {evaluation.left_hand_velocity_mps:.2f} m/s | "
        f"R hand {evaluation.right_hand_velocity_mps:.2f} m/s",
        (20, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (220, 220, 220),
        1,
    )
    y += 30

    if not evaluation.triggered_rules:
        cv2.putText(
            frame,
            "Rules: evaluating...",
            (20, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.52,
            (200, 200, 200),
            1,
        )
        return

    cv2.putText(frame, "Rules:", (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1)
    y += 22
    for rule in evaluation.triggered_rules[:8]:
        color = SEVERITY_COLORS.get(rule.severity, (255, 255, 255))
        cv2.putText(
            frame,
            f"- {rule.label}: {rule.message[:55]}",
            (20, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            color,
            1,
        )
        y += 20


def landmark_from_pose(pose, index: int) -> Landmark2D:
    lm = pose[index]
    return Landmark2D(x=lm.x, y=lm.y, z=getattr(lm, "z", 0.0), visibility=getattr(lm, "visibility", 1.0))


def build_motion_frame(pose, timestamp_ms: int, frame_index: int) -> MotionFrameData:
    return MotionFrameData(
        timestamp_ms=timestamp_ms,
        frame_index=frame_index,
        nose=landmark_from_pose(pose, NOSE),
        left_shoulder=landmark_from_pose(pose, LEFT_SHOULDER),
        right_shoulder=landmark_from_pose(pose, RIGHT_SHOULDER),
        left_elbow=landmark_from_pose(pose, LEFT_ELBOW),
        right_elbow=landmark_from_pose(pose, RIGHT_ELBOW),
        left_wrist=landmark_from_pose(pose, LEFT_WRIST),
        right_wrist=landmark_from_pose(pose, RIGHT_WRIST),
        left_hip=landmark_from_pose(pose, LEFT_HIP),
        right_hip=landmark_from_pose(pose, RIGHT_HIP),
    )
