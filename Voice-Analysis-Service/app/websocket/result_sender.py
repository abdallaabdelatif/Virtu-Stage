# sends the completed voice analysis result to the central Backend through
# voice-analyses endpoint once batch processing finishes.

import logging
import os
import httpx
from app.schemas.result import VoiceAnalysisResult
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
CENTRALIZED_BACKEND_URL = os.getenv("CENTRALIZED_BACKEND_URL", "http://localhost:8082")


async def send_result_to_central_backend(result: VoiceAnalysisResult) -> None:
    payload = {
        "session_id": result.session_id,
        "emotions": {
            "neutral": round(result.emotions.neutral, 4),
            "happy": round(result.emotions.happy, 4),
            "sad": round(result.emotions.sad, 4),
            "angry": round(result.emotions.angry, 4),
            # "dominant": result.emotions.dominant,
        },
        "anxiety_level": round(result.paralinguistic.anxiety_level, 4),
        "confidence_score": round(result.paralinguistic.confidence_score, 4),
        "clarity_level": round(result.paralinguistic.clarity_level, 4),
        "focus_score": round(result.paralinguistic.focus_score, 4),
        "pause_ratio": round(result.pauses.pause_ratio, 4),
        "pause_count": result.pauses.pause_count,
        "longest_pause_sec": round(result.pauses.longest_pause_seconds, 4),
        "filler_words_cnt": result.filler_word_count,
        "speech_rate_wpm": round(result.speech_rate_wpm, 4),
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
