from __future__ import annotations

from dataclasses import dataclass

from app.models.hand_data import HandTrack
from app.models.landmark import Landmark2D


# MediaPipe Pose upper-body landmark indices used by this prototype.
NOSE = 0
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16
LEFT_HIP = 23
RIGHT_HIP = 24


@dataclass
class MotionFrameData:
    timestamp_ms: int
    frame_index: int
    nose: Landmark2D
    left_shoulder: Landmark2D
    right_shoulder: Landmark2D
    left_elbow: Landmark2D
    right_elbow: Landmark2D
    left_wrist: Landmark2D
    right_wrist: Landmark2D
    left_hip: Landmark2D
    right_hip: Landmark2D
    left_hand: HandTrack | None = None
    right_hand: HandTrack | None = None

    def hand_for_side(self, side: str) -> HandTrack | None:
        return self.left_hand if side == "left" else self.right_hand

    def hand_tracking_point(self, side: str) -> Landmark2D:
        """Palm center when the hand is tracked; otherwise pose wrist."""
        hand = self.hand_for_side(side)
        if hand is not None:
            return hand.palm_center
        return self.left_wrist if side == "left" else self.right_wrist

    def hand_is_tracked(self, side: str) -> bool:
        hand = self.hand_for_side(side)
        return hand is not None and hand.is_tracked

    @property
    def mid_shoulder(self) -> Landmark2D:
        return Landmark2D(
            x=(self.left_shoulder.x + self.right_shoulder.x) / 2,
            y=(self.left_shoulder.y + self.right_shoulder.y) / 2,
            z=(self.left_shoulder.z + self.right_shoulder.z) / 2,
        )

    @property
    def mid_hip(self) -> Landmark2D:
        return Landmark2D(
            x=(self.left_hip.x + self.right_hip.x) / 2,
            y=(self.left_hip.y + self.right_hip.y) / 2,
            z=(self.left_hip.z + self.right_hip.z) / 2,
        )

    @property
    def shoulder_width_norm(self) -> float:
        from app.utils.geometry import distance_2d

        return distance_2d(self.left_shoulder, self.right_shoulder)
