from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

POSE_MODEL_CANDIDATES = [
    ROOT / "models" / "pose_landmarker_lite.task",
    ROOT.parent.parent / "Pose Estimation" / "pose_landmarker_lite.task",
    Path("pose_landmarker_lite.task"),
]

HAND_MODEL_CANDIDATES = [
    ROOT / "models" / "hand_landmarker.task",
    Path("hand_landmarker.task"),
]


def resolve_pose_model() -> str:
    return _resolve(POSE_MODEL_CANDIDATES, "Pose landmarker")


def resolve_hand_model() -> str:
    return _resolve(HAND_MODEL_CANDIDATES, "Hand landmarker")


def _resolve(candidates: list[Path], label: str) -> str:
    for path in candidates:
        if path.exists():
            return str(path.resolve())
    raise FileNotFoundError(f"{label} model not found. Place it under {ROOT / 'models'}")
