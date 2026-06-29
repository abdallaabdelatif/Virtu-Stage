from __future__ import annotations

import asyncio
import logging
import httpx

from app.config import CENTRALIZED_BACKEND_URL, INTERNAL_API_KEY
from app.models.motion_analysis_result import MotionAnalysisResult
from app.schemas.crud_payload import build_motion_analysis_create

logger = logging.getLogger(__name__)


async def send_result_to_central_backend(result: MotionAnalysisResult) -> None:
    body = build_motion_analysis_create(result).model_dump(mode="json")

    async with httpx.AsyncClient() as client:
        for attempt in range(1, 4):
            try:
                response = await client.post(
                    f"{CENTRALIZED_BACKEND_URL.rstrip('/')}/motion-analyses",
                    json=body,
                    headers={"X-Internal-API-Key": INTERNAL_API_KEY},
                    timeout=30.0,
                )
                response.raise_for_status()
                logger.info(
                    "Motion analysis result posted for session %s", result.session_id
                )
                return
            except httpx.HTTPError:
                logger.exception(
                    "Motion result callback attempt %s failed for session %s",
                    attempt,
                    result.session_id,
                )
                if attempt < 3:
                    await asyncio.sleep(2 ** (attempt - 1))
