# sends the completed voice analysis result to the central Backend through
# voice-analyses endpoint once batch processing finishes.

import logging
import os
import httpx
from app.schemas.result import VoiceAnalysisResult
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
CENTRALIZED_BACKEND_URL = os.getenv("CENTRALIZED_BACKEND_URL", "http://localhost:8000")


async def send_result_to_central_backend(result: VoiceAnalysisResult) -> None:
    payload = {
        "session_id": result.session_id,
        "emotions": {
            "neutral": result.emotions.neutral,
            "happy": result.emotions.happy,
            "sad": result.emotions.sad,
            "angry": result.emotions.angry,
            "dominant": result.emotions.dominant,
        },
        "anxiety_level": result.paralinguistic.anxiety_level,
        "confidence_score": result.paralinguistic.confidence_score,
        "clarity_level": result.paralinguistic.clarity_level,
        "focus_score": result.paralinguistic.focus_score,
        "pause_ratio": result.pauses.pause_ratio,
        "pause_count": result.pauses.pause_count,
        "longest_pause_second": result.pauses.longest_pause_seconds,
        "filler_words_count": result.filler_word_count,
        "speech_rate_wpm": result.speech_rate_wpm,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{CENTRALIZED_BACKEND_URL}/voice-analyses",
                json=payload,
                timeout=10.0,
            )
            response.raise_for_status()
            logger.info(
                "Voice analysis result posted for session %s", result.session_id
            )
        except httpx.HTTPError:
            logger.exception(
                "Failed to post voice analysis result for session %s", result.session_id
            )
