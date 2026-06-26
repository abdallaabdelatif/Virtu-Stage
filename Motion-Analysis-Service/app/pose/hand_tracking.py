from __future__ import annotations

from app.models.hand_data import (
    FINGERTIP_INDICES,
    PALM_INDICES,
    HandTrack,
)
from app.models.landmark import Landmark2D
from app.models.motion_frame_data import MotionFrameData


def landmark_from_normalized(lm) -> Landmark2D:
    return Landmark2D(
        x=lm.x,
        y=lm.y,
        z=getattr(lm, "z", 0.0),
        visibility=getattr(lm, "visibility", 1.0),
    )


def _palm_center(landmarks: list[Landmark2D]) -> Landmark2D:
    pts = [landmarks[i] for i in PALM_INDICES]
    return Landmark2D(
        x=sum(p.x for p in pts) / len(pts),
        y=sum(p.y for p in pts) / len(pts),
        z=sum(p.z for p in pts) / len(pts),
        visibility=min(p.visibility for p in pts),
    )


def hand_track_from_landmarks(landmarks: list, side: str) -> HandTrack:
    lms = tuple(landmark_from_normalized(lm) for lm in landmarks)
    tips = tuple(lms[i] for i in FINGERTIP_INDICES)
    return HandTrack(
        side=side,
        wrist=lms[0],
        palm_center=_palm_center(list(lms)),
        fingertips=tips,
        landmarks=lms,
    )


def extract_hands(hand_result) -> dict[str, HandTrack]:
    """Map HandLandmarker output to presenter left/right hands."""
    hands: dict[str, HandTrack] = {}
    if not hand_result or not hand_result.hand_landmarks:
        return hands

    for idx, hand_landmarks in enumerate(hand_result.hand_landmarks):
        if not hand_result.handedness or idx >= len(hand_result.handedness):
            continue
        category = hand_result.handedness[idx][0].category_name.lower()
        side = "left" if "left" in category else "right"
        hands[side] = hand_track_from_landmarks(hand_landmarks, side)

    return hands


def attach_hands(frame: MotionFrameData, hands: dict[str, HandTrack]) -> MotionFrameData:
    return MotionFrameData(
        timestamp_ms=frame.timestamp_ms,
        frame_index=frame.frame_index,
        nose=frame.nose,
        left_shoulder=frame.left_shoulder,
        right_shoulder=frame.right_shoulder,
        left_elbow=frame.left_elbow,
        right_elbow=frame.right_elbow,
        left_wrist=frame.left_wrist,
        right_wrist=frame.right_wrist,
        left_hip=frame.left_hip,
        right_hip=frame.right_hip,
        left_hand=hands.get("left"),
        right_hand=hands.get("right"),
    )
