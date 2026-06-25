from __future__ import annotations

import uuid

from app.models.motion_analysis_result import MotionAnalysisResult
from app.schemas.motion_schema import FidgetingLevel, MotionAnalysisCreate


def build_motion_analysis_create(result: MotionAnalysisResult) -> MotionAnalysisCreate:
    payload = result.to_crud_payload()
    return MotionAnalysisCreate(
        session_id=uuid.UUID(str(payload["session_id"])),
        fidgeting_level=FidgetingLevel(result.metrics.fidgeting_level),
        **{
            k: v
            for k, v in payload.items()
            if k not in ("session_id", "fidgeting_level")
        },
    )
