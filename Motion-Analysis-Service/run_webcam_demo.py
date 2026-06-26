"""
Local development tool — NOT the production input path.

Production uses WebSocket frame batches (uvicorn app.main:app).
Uses the same LivePreview overlay as the VR / WebSocket pipeline.
Press Q in the preview window to hide the overlay (analysis continues).
"""

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from app.analysis.motion_pipeline import MotionAnalysisPipeline
from app.models.motion_frame_data import MotionFrameData
from app.reporting.session_report import print_presentation_assessment, save_session_report
from app.visualization.live_preview import LivePreview
from app.visualization.preview_frame import PreviousFrameHolder, preview_motion_frame


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Offline motion analysis on a video file.")
    parser.add_argument("--video", type=Path, required=True, help="Path to a video file")
    return parser.parse_args()


def run_video_demo(video_path: Path) -> None:
    import cv2

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video file: {video_path}")

    session_id = str(uuid.uuid4())
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or fps > 120:
        fps = 30.0

    pipeline = MotionAnalysisPipeline()
    preview = LivePreview()
    motion_frames: list[MotionFrameData] = []
    previous = PreviousFrameHolder()
    frame_index = 0
    timestamp_ms = 0

    print(f"Session ID : {session_id}")
    print(f"FPS        : {fps:.1f}")
    print(f"Preview    : on (Q to hide overlay)\n")

    try:
        while cap.isOpened():
            ret, bgr = cap.read()
            if not ret:
                break

            motion_frame = pipeline.processor.process_bgr(bgr, timestamp_ms, frame_index)
            preview_motion_frame(
                pipeline,
                preview,
                motion_frame,
                motion_frames,
                previous,
                fps=fps,
                frame_index=frame_index,
                timestamp_ms=timestamp_ms,
                bgr=bgr,
            )
            frame_index += 1
            timestamp_ms += int(1000 / fps)
    finally:
        cap.release()
        preview.close()
        pipeline.close()

    if not motion_frames:
        print("No reliable pose frames captured. Nothing to analyze.")
        return

    result = pipeline.run_from_motion_frames(session_id, motion_frames, fps=fps)
    output_path = save_session_report(result, ROOT / "output")
    print_presentation_assessment(
        result, frames_analyzed=len(motion_frames), output_path=output_path
    )


def main() -> None:
    args = parse_args()
    run_video_demo(args.video.resolve())


if __name__ == "__main__":
    main()
