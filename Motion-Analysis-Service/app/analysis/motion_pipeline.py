from __future__ import annotations

import logging

from app.analysis.frame_processor import FrameProcessor
from app.frame.vr_batch import VRFrame
from app.models.motion_analysis_result import MotionAnalysisResult
from app.models.motion_analysis_service import MotionAnalysisService
from app.models.motion_frame_data import MotionFrameData
from app.models.motion_rule_engine import MotionRuleEngine

logger = logging.getLogger(__name__)


class MotionAnalysisPipeline:
    def __init__(self) -> None:
        self._processor = FrameProcessor()
        self._service = MotionAnalysisService(MotionRuleEngine())

    @property
    def processor(self) -> FrameProcessor:
        return self._processor

    @property
    def service(self) -> MotionAnalysisService:
        return self._service

    def close(self) -> None:
        self._processor.close()

    def run(self, session_id: str, vr_frames: list[VRFrame]) -> MotionAnalysisResult:
        self._processor.reset_session()
        motion_frames = self._extract_from_vr(vr_frames)
        fps = self._estimate_fps(vr_frames)
        return self._analyze(session_id, motion_frames, fps)

    def run_from_motion_frames(
        self,
        session_id: str,
        motion_frames: list[MotionFrameData],
        fps: float,
    ) -> MotionAnalysisResult:
        return self._analyze(session_id, motion_frames, fps)

    def _extract_from_vr(self, vr_frames: list[VRFrame]) -> list[MotionFrameData]:
        motion_frames: list[MotionFrameData] = []
        for vr_frame in vr_frames:
            motion_frame = self._processor.process_jpeg(
                vr_frame.jpeg,
                vr_frame.timestamp_ms,
                vr_frame.index,
            )
            if motion_frame is not None:
                motion_frames.append(motion_frame)
        return motion_frames

    def _analyze(
        self,
        session_id: str,
        motion_frames: list[MotionFrameData],
        fps: float,
    ) -> MotionAnalysisResult:
        if not motion_frames:
            raise ValueError("No reliable pose frames to analyze")

        logger.info(
            "Session %s: analyzing %d frames at %.1f fps",
            session_id,
            len(motion_frames),
            fps,
        )
        return self._service.analyze_session(motion_frames, fps=fps, session_id=session_id)

    @staticmethod
    def _estimate_fps(frames: list[VRFrame]) -> float:
        if len(frames) < 2:
            return 30.0
        duration_ms = max(frames[-1].timestamp_ms - frames[0].timestamp_ms, 1)
        return max(1.0, min(60.0, (len(frames) - 1) * 1000.0 / duration_ms))
