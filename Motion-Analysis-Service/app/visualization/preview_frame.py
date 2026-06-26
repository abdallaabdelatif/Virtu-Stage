from __future__ import annotations

import numpy as np

from app.analysis.motion_pipeline import MotionAnalysisPipeline
from app.frame.vr_batch import VRFrame
from app.models.motion_frame_data import MotionFrameData
from app.visualization.live_preview import LivePreview


class PreviousFrameHolder:
    def __init__(self) -> None:
        self.value: MotionFrameData | None = None


def preview_vr_frames(
    pipeline: MotionAnalysisPipeline,
    preview: LivePreview,
    vr_frames: list[VRFrame],
    all_vr_frames: list[VRFrame],
    motion_frames: list[MotionFrameData],
    previous: PreviousFrameHolder,
) -> None:
    """Process a VR batch: landmarks, live overlay, accumulate for final session score."""
    fps = MotionAnalysisPipeline._estimate_fps(all_vr_frames)
    for vr_frame in vr_frames:
        motion_frame = pipeline.processor.process_jpeg(
            vr_frame.jpeg,
            vr_frame.timestamp_ms,
            vr_frame.index,
        )
        preview_motion_frame(
            pipeline,
            preview,
            motion_frame,
            motion_frames,
            previous,
            fps=fps,
            frame_index=vr_frame.index,
            timestamp_ms=vr_frame.timestamp_ms,
            jpeg=vr_frame.jpeg,
        )


def preview_motion_frame(
    pipeline: MotionAnalysisPipeline,
    preview: LivePreview | None,
    motion_frame: MotionFrameData | None,
    motion_frames: list[MotionFrameData],
    previous: PreviousFrameHolder,
    *,
    fps: float,
    frame_index: int,
    timestamp_ms: int,
    bgr: np.ndarray | None = None,
    jpeg: bytes | None = None,
) -> None:
    if motion_frame is None:
        return

    motion_frames.append(motion_frame)
    if preview is None or not preview.is_enabled:
        previous.value = motion_frame
        return

    evaluation = pipeline.service.evaluate_frame(
        motion_frame, previous.value, fps
    )
    if bgr is not None:
        preview.show(
            bgr,
            motion_frame,
            evaluation,
            frame_index=frame_index,
            timestamp_ms=timestamp_ms,
            fps=fps,
        )
    elif jpeg is not None:
        preview.show_jpeg(
            jpeg,
            motion_frame,
            evaluation,
            frame_index=frame_index,
            timestamp_ms=timestamp_ms,
            fps=fps,
        )
    previous.value = motion_frame
