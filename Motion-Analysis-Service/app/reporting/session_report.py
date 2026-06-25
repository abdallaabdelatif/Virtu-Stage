from __future__ import annotations

import json
from pathlib import Path

from app.models.motion_analysis_result import MotionAnalysisResult
from app.schemas.crud_payload import build_motion_analysis_create


def save_session_report(result: MotionAnalysisResult, output_dir: Path) -> Path:
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"motion_analysis_{result.session_id[:8]}.json"
    report = result.to_display_dict()
    report["crud_payload"] = build_motion_analysis_create(result).model_dump(mode="json")
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    return output_path


def print_presentation_assessment(
    result: MotionAnalysisResult,
    *,
    frames_analyzed: int,
    output_path: Path | None = None,
) -> None:
    print("=" * 60)
    print("SESSION COMPLETE — Presentation Assessment")
    print("=" * 60)
    print(f"Frames analyzed  : {frames_analyzed}")
    print(f"Dominant posture : {result.dominant_posture_type}")
    print()
    pa = result.presentation
    print(f"Overall          : {pa.overall.value.upper()}")
    print(f"  → {pa.overall_meaning}")
    print()
    print("Dimensions:")
    for label, rating, meaning in (
        ("Posture", pa.posture, pa.posture_meaning),
        ("Gaze", pa.gaze, pa.gaze_meaning),
        ("Gestures", pa.gestures, pa.gestures_meaning),
        ("Composure", pa.composure, pa.composure_meaning),
        ("Stability", pa.stability, pa.stability_meaning),
    ):
        print(f"  {label:12} {rating.value:12} — {meaning}")
    print()
    print(f"Sudden events    : {len(result.metrics.sudden_index)}")
    print(f"Repetitive groups: {len(result.metrics.repetitive_index)}")
    print(f"Hand near face   : {result.metrics.hand_near_face_ratio * 100:.0f}% of frames")
    print(f"Hand tracking    : {result.metrics.hand_tracking_ratio * 100:.0f}% of frames")
    print(f"Looking down     : {result.metrics.looking_down_ratio * 100:.0f}% of frames")
    print()
    print("Recommendations:")
    for rec in result.recommendations:
        print(f"  • {rec}")
    if output_path is not None:
        print()
        print(f"Full report saved to: {output_path}")
