from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Landmark2D:
    x: float
    y: float
    z: float = 0.0
    visibility: float = 1.0
