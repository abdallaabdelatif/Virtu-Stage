from __future__ import annotations

import logging
import os

import httpx
from dotenv import load_dotenv

from app.models.motion_analysis_result import MotionAnalysisResult
from app.schemas.crud_payload import build_motion_analysis_create

load_dotenv()
logger = logging.getLogger(__name__)

CENTRALIZED_BACKEND_URL = os.getenv("CENTRALIZED_BACKEND_URL", "http://localhost:8082")


async def send_result_to_central_backend(result: MotionAnalysisResult) -> None:
    body = build_motion_analysis_create(result).model_dump(mode="json")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{CENTRALIZED_BACKEND_URL.rstrip('/')}/motion-analyses",
                json=body,
                timeout=30.0,
            )
            response.raise_for_status()
            logger.info("Motion analysis result posted for session %s", result.session_id)
        except httpx.HTTPError:
            logger.exception(
                "Failed to post motion analysis result for session %s", result.session_id
            )