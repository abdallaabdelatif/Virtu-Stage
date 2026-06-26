"""
Local development tool — NOT the production input path.

Production uses WebSocket frame batches (uvicorn app.main:app).
This script reuses MotionAnalysisPipeline + FrameProcessor for offline video files.
Use --preview to open a live overlay window; default is headless analysis.
"""

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from app.analysis.motion_pipeline import MotionAnalysisPipeline
from app.models.motion_frame_data import MotionFrameData
from app.reporting.session_report import print_presentation_assessment, save_session_report
from app.visualization.overlay import draw_overlay, draw_skeleton


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Offline motion analysis on a video file.")
    parser.add_argument("--video", type=Path, required=True, help="Path to a video file")
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Show live skeleton overlay window (optional)",
    )
    return parser.parse_args()


def run_headless_video(video_path: Path, *, preview: bool) -> None:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video file: {video_path}")

    session_id = str(uuid.uuid4())
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or fps > 120:
        fps = 30.0

    pipeline = MotionAnalysisPipeline()
    motion_frames: list[MotionFrameData] = []
    previous_frame: MotionFrameData | None = None
    frame_index = 0
    timestamp_ms = 0

    print(f"Session ID : {session_id}")
    print(f"FPS        : {fps:.1f}")
    print(f"Mode       : {'preview' if preview else 'headless'}\n")

    try:
        while cap.isOpened():
            ret, bgr = cap.read()
            if not ret:
                break

            motion_frame = pipeline.processor.process_bgr(bgr, timestamp_ms, frame_index)
            if motion_frame is not None:
                motion_frames.append(motion_frame)

            if preview and motion_frame is not None:
                evaluation = pipeline.service.evaluate_frame(
                    motion_frame, previous_frame, fps
                )
                draw_skeleton(bgr, motion_frame)
                draw_overlay(bgr, evaluation, frame_index, frame_index / fps)
                cv2.imshow("VirtuStage Motion Analysis (dev preview)", bgr)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
                previous_frame = motion_frame

            frame_index += 1
            timestamp_ms += int(1000 / fps)
    finally:
        cap.release()
        if preview:
            cv2.destroyAllWindows()
        pipeline.close()

    if not motion_frames:
        print("No reliable pose frames captured. Nothing to analyze.")
        return

    result = pipeline.run_from_motion_frames(motion_frames, fps=fps, session_id=session_id)
    output_path = save_session_report(result, ROOT / "output")
    print_presentation_assessment(
        result, frames_analyzed=len(motion_frames), output_path=output_path
    )


def main() -> None:
    args = parse_args()
    run_headless_video(args.video.resolve(), preview=args.preview)


if __name__ == "__main__":
    main()
