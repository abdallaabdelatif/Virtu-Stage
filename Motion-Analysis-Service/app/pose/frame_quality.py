from __future__ import annotations

from app.models.motion_frame_data import MotionFrameData

MIN_LANDMARK_VISIBILITY = 0.35
MIN_SHOULDER_WIDTH = 0.05
MAX_SHOULDER_WIDTH = 0.75


def is_tracking_reliable(frame: MotionFrameData) -> bool:
    """Reject frames where pose tracking is too weak or body scale is implausible."""
    landmarks = (
        frame.nose,
        frame.left_shoulder,
        frame.right_shoulder,
        frame.left_wrist,
        frame.right_wrist,
        frame.left_hip,
        frame.right_hip,
    )
    if any(lm.visibility < MIN_LANDMARK_VISIBILITY for lm in landmarks):
        return False

    width = frame.shoulder_width_norm
    return MIN_SHOULDER_WIDTH <= width <= MAX_SHOULDER_WIDTH
