from __future__ import annotations

from app.models.hand_data import HandTrack
from app.models.motion_frame_data import Landmark2D, MotionFrameData


class LandmarkSmoother:
    """
    Exponential moving average (EMA) filter per landmark.
    Reduces MediaPipe jitter before rules and velocity calculations run.
    """

    def __init__(
        self,
        alpha_nose: float = 0.35,
        alpha_torso: float = 0.25,
        alpha_limbs: float = 0.30,
    ) -> None:
        self._alpha = {
            "nose": alpha_nose,
            "torso": alpha_torso,
            "limbs": alpha_limbs,
        }
        self._state: dict[str, Landmark2D] = {}

    def smooth(self, frame: MotionFrameData) -> MotionFrameData:
        return MotionFrameData(
            timestamp_ms=frame.timestamp_ms,
            frame_index=frame.frame_index,
            nose=self._smooth_landmark("nose", frame.nose, self._alpha["nose"]),
            left_shoulder=self._smooth_landmark(
                "left_shoulder", frame.left_shoulder, self._alpha["torso"]
            ),
            right_shoulder=self._smooth_landmark(
                "right_shoulder", frame.right_shoulder, self._alpha["torso"]
            ),
            left_elbow=self._smooth_landmark(
                "left_elbow", frame.left_elbow, self._alpha["limbs"]
            ),
            right_elbow=self._smooth_landmark(
                "right_elbow", frame.right_elbow, self._alpha["limbs"]
            ),
            left_wrist=self._smooth_landmark(
                "left_wrist", frame.left_wrist, self._alpha["limbs"]
            ),
            right_wrist=self._smooth_landmark(
                "right_wrist", frame.right_wrist, self._alpha["limbs"]
            ),
            left_hip=self._smooth_landmark("left_hip", frame.left_hip, self._alpha["torso"]),
            right_hip=self._smooth_landmark(
                "right_hip", frame.right_hip, self._alpha["torso"]
            ),
            left_hand=self._smooth_hand("left", frame.left_hand),
            right_hand=self._smooth_hand("right", frame.right_hand),
        )

    def _smooth_hand(self, side: str, hand: HandTrack | None) -> HandTrack | None:
        if hand is None:
            return None

        from app.models.hand_data import FINGERTIP_INDICES, PALM_INDICES

        smoothed = tuple(
            self._smooth_landmark(f"{side}_hand_{i}", lm, self._alpha["limbs"])
            for i, lm in enumerate(hand.landmarks)
        )
        palm_pts = [smoothed[i] for i in PALM_INDICES]
        palm_center = Landmark2D(
            x=sum(p.x for p in palm_pts) / len(palm_pts),
            y=sum(p.y for p in palm_pts) / len(palm_pts),
            z=sum(p.z for p in palm_pts) / len(palm_pts),
            visibility=min(p.visibility for p in palm_pts),
        )
        return HandTrack(
            side=side,
            wrist=smoothed[0],
            palm_center=palm_center,
            fingertips=tuple(smoothed[i] for i in FINGERTIP_INDICES),
            landmarks=smoothed,
        )

    def _smooth_landmark(self, key: str, current: Landmark2D, alpha: float) -> Landmark2D:
        previous = self._state.get(key)
        if previous is None:
            self._state[key] = current
            return current

        smoothed = Landmark2D(
            x=alpha * current.x + (1 - alpha) * previous.x,
            y=alpha * current.y + (1 - alpha) * previous.y,
            z=alpha * current.z + (1 - alpha) * previous.z,
            visibility=current.visibility,
        )
        self._state[key] = smoothed
        return smoothed

    def reset(self) -> None:
        self._state.clear()
