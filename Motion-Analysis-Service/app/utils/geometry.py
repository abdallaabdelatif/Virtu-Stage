from __future__ import annotations

import math
from typing import TYPE_CHECKING

from app.models.motion_frame_data import Landmark2D, MotionFrameData


def distance_2d(a: Landmark2D, b: Landmark2D) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


def distance_3d(a: Landmark2D, b: Landmark2D) -> float:
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2)


def norm_to_meters(distance_norm: float, shoulder_width_norm: float, shoulder_width_m: float = 0.40) -> float:
    if shoulder_width_norm < 1e-6:
        return 0.0
    return (distance_norm / shoulder_width_norm) * shoulder_width_m


def velocity_mps(
    current: Landmark2D,
    previous: Landmark2D,
    dt_seconds: float,
    shoulder_width_norm: float,
    shoulder_width_m: float = 0.40,
    max_mps: float = 1.5,
) -> float:
    if dt_seconds <= 0:
        return 0.0
    dist_norm = distance_2d(current, previous)
    dist_m = norm_to_meters(dist_norm, shoulder_width_norm, shoulder_width_m)
    raw = dist_m / dt_seconds
    return min(raw, max_mps)


def angle_degrees_from_vertical(top: Landmark2D, bottom: Landmark2D) -> float:
    dx = top.x - bottom.x
    dy = top.y - bottom.y
    return abs(math.degrees(math.atan2(dx, -dy)))


def head_tilt_from_vertical_degrees(top: Landmark2D, bottom: Landmark2D) -> float:
    """
    Angle of the head-neck line (bottom -> top) away from vertical.
    Uses 2D image coordinates only — stable on webcam (no noisy depth).
    Upright: ~0-10°. Forward/side tilt increases the angle.
    """
    dx = top.x - bottom.x
    dy = top.y - bottom.y
    magnitude = math.hypot(dx, dy)
    if magnitude < 1e-6:
        return 0.0
    cos_angle = clamp(-dy / magnitude, -1.0, 1.0)
    return math.degrees(math.acos(cos_angle))


def head_pitch_degrees(nose: Landmark2D, mid_shoulder: Landmark2D) -> float:
    """
    How far the nose sits below shoulder level (looking down).
    Returns 0 when nose is at or above shoulders.
    """
    dy = nose.y - mid_shoulder.y
    if dy <= 0:
        return 0.0
    dx = abs(nose.x - mid_shoulder.x)
    return math.degrees(math.atan2(dy, dx + 0.04))


def posture_forward_lean_degrees(frame: MotionFrameData) -> float:
    """
    Rule 1 metric: head relative to shoulders + torso upright alignment.
    Weighted 2D-only estimate — avoids unreliable MediaPipe z jitter.
    """
    head_tilt = head_tilt_from_vertical_degrees(frame.nose, frame.mid_shoulder)
    spine_tilt = spine_tilt_degrees(frame.mid_shoulder, frame.mid_hip)
    return 0.45 * head_tilt + 0.55 * spine_tilt


def forward_lean_degrees(nose: Landmark2D, mid_shoulder: Landmark2D) -> float:
    """Backward-compatible alias — use posture metrics on full frame when possible."""
    return head_tilt_from_vertical_degrees(nose, mid_shoulder)


def spine_tilt_degrees(mid_shoulder: Landmark2D, mid_hip: Landmark2D) -> float:
    return angle_degrees_from_vertical(mid_shoulder, mid_hip)


def shoulder_height_diff_ratio(
    left_shoulder: Landmark2D,
    right_shoulder: Landmark2D,
    shoulder_width_norm: float,
) -> float:
    """Shoulder height asymmetry as a fraction of shoulder width (scale-invariant)."""
    if shoulder_width_norm < 1e-6:
        return 0.0
    return abs(left_shoulder.y - right_shoulder.y) / shoulder_width_norm


def shoulder_height_diff_cm(
    left_shoulder: Landmark2D,
    right_shoulder: Landmark2D,
    shoulder_width_norm: float,
    shoulder_width_m: float = 0.40,
) -> float:
    return shoulder_height_diff_ratio(
        left_shoulder, right_shoulder, shoulder_width_norm
    ) * shoulder_width_m * 100


def gesture_space_ratio(hand: Landmark2D, shoulder: Landmark2D, shoulder_width_norm: float) -> float:
    if shoulder_width_norm < 1e-6:
        return 0.0
    return distance_2d(hand, shoulder) / shoulder_width_norm


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def normalize_score(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.0
    return clamp((value - low) / (high - low))


def neck_torso_opening_degrees(
    mid_hip: Landmark2D, mid_shoulder: Landmark2D, nose: Landmark2D
) -> float:
    """
    Angle between torso (hip→shoulder) and neck (shoulder→nose) at the shoulders.
    Upright: vectors align (~0–15°). Reclining: head tilts back, opening widens.
    """
    v_torso = (mid_shoulder.x - mid_hip.x, mid_shoulder.y - mid_hip.y)
    v_neck = (nose.x - mid_shoulder.x, nose.y - mid_shoulder.y)
    mag_t = math.hypot(*v_torso)
    mag_n = math.hypot(*v_neck)
    if mag_t < 1e-6 or mag_n < 1e-6:
        return 0.0
    cos_angle = clamp((v_torso[0] * v_neck[0] + v_torso[1] * v_neck[1]) / (mag_t * mag_n), -1.0, 1.0)
    return math.degrees(math.acos(cos_angle))


def posture_backward_lean_degrees(frame: MotionFrameData) -> float:
    """
    Detect reclining / leaning backward using neck–torso opening angle.

    Do NOT use head-above-shoulder gap — every upright person has the head
    well above shoulders in image coordinates, which caused false positives.
    """
    forward = posture_forward_lean_degrees(frame)
    if forward > 14.0:
        return 0.0

    opening = neck_torso_opening_degrees(frame.mid_hip, frame.mid_shoulder, frame.nose)
    # Frontal webcam: aligned upright ~0–18°; clear recline typically > 28°.
    excess = max(0.0, opening - 26.0)
    if excess <= 0.0:
        return 0.0

    return min(35.0, excess * 1.6)


def hand_to_face_distance_ratio(frame: MotionFrameData, side: str) -> float:
    """
    Normalized closest distance from hand to face (lower = nearer).
    Uses palm + fingertips when hand landmarker is active; falls back to wrist.
    """
    sw = frame.shoulder_width_norm
    if sw < 1e-6:
        return 999.0

    hand = frame.hand_for_side(side)
    if hand is not None:
        distances = [distance_2d(point, frame.nose) for point in hand.proximity_points()]
        return min(distances) / sw

    wrist = frame.left_wrist if side == "left" else frame.right_wrist
    return distance_2d(wrist, frame.nose) / sw


def hand_near_face_detail(frame: MotionFrameData, side: str, max_ratio: float) -> tuple[bool, str, float]:
    """Returns (is_near, closest_part_label, distance_ratio)."""
    sw = frame.shoulder_width_norm
    if sw < 1e-6:
        return False, "wrist", 999.0

    hand = frame.hand_for_side(side)
    if hand is not None:
        best_ratio = 999.0
        best_label = "palm"
        for label, point in (
            ("palm", hand.palm_center),
            ("thumb", hand.fingertips[0]),
            ("index", hand.fingertips[1]),
            ("middle", hand.fingertips[2]),
            ("ring", hand.fingertips[3]),
            ("pinky", hand.fingertips[4]),
        ):
            ratio = distance_2d(point, frame.nose) / sw
            if ratio < best_ratio:
                best_ratio = ratio
                best_label = label
        return best_ratio < max_ratio, best_label, best_ratio

    wrist = frame.left_wrist if side == "left" else frame.right_wrist
    ratio = distance_2d(wrist, frame.nose) / sw
    return ratio < max_ratio, "wrist", ratio


def is_hand_near_face(frame: MotionFrameData, max_ratio: float = 0.45) -> bool:
    """MIT: minimize distracting gestures — hands/fingers near face read as nervousness."""
    left_near, _, _ = hand_near_face_detail(frame, "left", max_ratio)
    right_near, _, _ = hand_near_face_detail(frame, "right", max_ratio)
    return left_near or right_near
