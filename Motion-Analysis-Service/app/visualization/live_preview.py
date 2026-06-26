from __future__ import annotations

import cv2
import numpy as np

from app.models.motion_analysis_service import FrameEvaluation
from app.models.motion_frame_data import MotionFrameData
from app.visualization.overlay import draw_overlay, draw_skeleton

WINDOW_TITLE = "VirtuStage Motion Analysis"


class LivePreview:

    def __init__(self) -> None:
        self._enabled = True

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def show(
        self,
        bgr: np.ndarray,
        motion_frame: MotionFrameData,
        evaluation: FrameEvaluation,
        *,
        frame_index: int,
        timestamp_ms: int,
        fps: float,
    ) -> None:
        if not self._enabled:
            return

        frame = bgr.copy()
        session_seconds = timestamp_ms / 1000.0 if timestamp_ms else frame_index / max(fps, 1.0)
        draw_skeleton(frame, motion_frame)
        draw_overlay(frame, evaluation, frame_index, session_seconds)
        cv2.imshow(WINDOW_TITLE, frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            self._enabled = False
            cv2.destroyWindow(WINDOW_TITLE)

    def show_jpeg(
        self,
        jpeg: bytes,
        motion_frame: MotionFrameData,
        evaluation: FrameEvaluation,
        *,
        frame_index: int,
        timestamp_ms: int,
        fps: float,
    ) -> None:
        bgr = cv2.imdecode(np.frombuffer(jpeg, dtype=np.uint8), cv2.IMREAD_COLOR)
        if bgr is None:
            return
        self.show(
            bgr,
            motion_frame,
            evaluation,
            frame_index=frame_index,
            timestamp_ms=timestamp_ms,
            fps=fps,
        )

    def close(self) -> None:
        cv2.destroyAllWindows()
