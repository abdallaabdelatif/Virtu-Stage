from __future__ import annotations

from dataclasses import dataclass

from app.models.landmark import Landmark2D

# MediaPipe Hand Landmarker indices (21 landmarks per hand).
WRIST = 0
THUMB_TIP = 4
INDEX_TIP = 8
MIDDLE_TIP = 12
RING_TIP = 16
PINKY_TIP = 20
FINGERTIP_INDICES = (THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP)
PALM_INDICES = (0, 5, 9, 13, 17)

HAND_CONNECTIONS = (
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),
    (0, 9),
    (9, 10),
    (10, 11),
    (11, 12),
    (0, 13),
    (13, 14),
    (14, 15),
    (15, 16),
    (0, 17),
    (17, 18),
    (18, 19),
    (19, 20),
    (5, 9),
    (9, 13),
    (13, 17),
)


@dataclass(frozen=True)
class HandTrack:
    """21-point hand skeleton from MediaPipe Hand Landmarker."""

    side: str
    wrist: Landmark2D
    palm_center: Landmark2D
    fingertips: tuple[Landmark2D, Landmark2D, Landmark2D, Landmark2D, Landmark2D]
    landmarks: tuple[Landmark2D, ...]

    @property
    def is_tracked(self) -> bool:
        return len(self.landmarks) == 21

    def proximity_points(self) -> list[Landmark2D]:
        """Points used for face proximity — palm + all fingertips."""
        return [self.palm_center, *self.fingertips]
