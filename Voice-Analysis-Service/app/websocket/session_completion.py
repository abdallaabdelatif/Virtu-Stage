from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
import logging
from typing import Any
from app.analysis import pipeline
from app.audio.audio_buffer import AudioBuffer
from app.audio.transcript_buffer import TranscriptBuffer
from app.config import VOICE_ANALYSIS_RESULT_CALLBACK_URL
from app.feedback import trait_feedback
from app.scoring import trait_scorer
from app.websocket import result_sender


logger = logging.getLogger(__name__)


@dataclass
class SessionAnalysisState:
    session_id: str
    audio_closed: bool = False
    transcript_closed: bool = False
    result_callback_url: str | None = None
    result_sent: bool = False
    result_sending: bool = False
    transcript_text: str = ""
    audio: dict[str, Any] = field(default_factory=dict)
    transcript: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    audio_done: asyncio.Event = field(default_factory=asyncio.Event)
    transcript_done: asyncio.Event = field(default_factory=asyncio.Event)


_session_results: dict[str, SessionAnalysisState] = {}  # shared memory for all active
_session_lock = asyncio.Lock()  # to prevent race conditions


async def register_result_callback(session_id: str) -> None:
    async with _session_lock:
        state = _get_state(session_id)
        state.result_callback_url = VOICE_ANALYSIS_RESULT_CALLBACK_URL


async def on_audio_socket_closed(session_id: str, buffer: AudioBuffer) -> None:
    async with _session_lock:
        state = _get_state(session_id)
        state.audio_closed = True

    if not buffer.has_audio:
        logger.warning("Audio socket closed without audio for session %s", session_id)
        async with _session_lock:
            state = _get_state(session_id)
            state.audio_done.set()
        await send_result_if_ready(session_id)
        return

    logger.info("Starting audio feature extraction for session %s", session_id)
    audio_result = await pipeline.analyze_audio_buffer(buffer)

    async with _session_lock:
        state = _get_state(session_id)
        state.audio = audio_result
        state.audio_done.set()

        if audio_result.get("error"):
            state.errors.append(audio_result["error"])

    logger.info("Finished audio feature extraction for session %s", session_id)
    await send_result_if_ready(session_id)


async def on_transcript_socket_closed(
    session_id: str,
    buffer: TranscriptBuffer,
) -> None:
    transcript_text = buffer.full_transcript()

    async with _session_lock:
        state = _get_state(session_id)
        state.transcript_closed = True
        state.transcript_text = transcript_text
        audio_done = state.audio_done

    if not buffer.has_text:
        logger.warning(
            "Transcript socket closed without transcript text for session %s",
            session_id,
        )
        async with _session_lock:
            _get_state(session_id).transcript_done.set()
        await send_result_if_ready(session_id)
        return

    logger.info("Starting transcript feature extraction for session %s", session_id)
    transcript_result = await pipeline.analyze_transcript_buffer(
        buffer,
        audio_done=audio_done,
        get_audio_result=lambda: _get_audio_result(session_id),
    )

    async with _session_lock:
        state = _get_state(session_id)
        state.transcript = transcript_result
        state.transcript_done.set()
        if transcript_result.get("error"):
            state.errors.append(transcript_result["error"])

    logger.info("Finished transcript feature extraction for session %s", session_id)
    await send_result_if_ready(session_id)


async def get_session_analysis(session_id: str) -> dict[str, Any] | None:
    async with _session_lock:
        state = _session_results.get(session_id)
        if state is None:
            return None
        return {
            "session_id": state.session_id,
            "transcript_closed": state.transcript_closed,
            "result_sent": state.result_sent,
            "analysis": trait_scorer.score_final_analysis(
                state.audio,
                state.transcript,
            ),
            "errors": list(state.errors),
        }


async def send_result_if_ready(session_id: str) -> bool:
    async with _session_lock:
        state = _session_results.get(session_id)
        if state is None:
            return False
        if state.result_sent or state.result_sending or not state.result_callback_url:
            return False
        if not (state.audio_closed and state.transcript_closed):
            return False
        if not state.audio_done.is_set():
            return False
        if not state.transcript_done.is_set():
            return False

        callback_url = state.result_callback_url
        payload = _flat_result_payload(
            session_id=state.session_id,
            analysis=trait_scorer.score_final_analysis(
                state.audio,
                state.transcript,
            ),
            feedback=trait_feedback.build_trait_feedback(
                state.audio,
                state.transcript,
            ),
        )
        state.result_sending = True

    try:
        posted = await result_sender.post_result(callback_url, payload)
    except Exception:
        logger.exception(
            "Unexpected result callback failure for session %s", session_id
        )
        posted = False

    async with _session_lock:
        state = _session_results.get(session_id)
        if state is not None:
            state.result_sending = False
            state.result_sent = posted
            if not posted:
                state.errors.append(f"result_callback_failed: {callback_url}")
    return posted


def _get_state(session_id: str) -> SessionAnalysisState:
    if session_id not in _session_results:
        _session_results[session_id] = SessionAnalysisState(session_id=session_id)
    return _session_results[session_id]


def _get_audio_result(session_id: str) -> dict[str, Any]:
    state = _session_results.get(session_id)
    if state is not None:
        return state.audio
    return {}


def _flat_result_payload(
    session_id: str,
    analysis: dict[str, Any],
    feedback: dict[str, str],
) -> dict[str, Any]:
    traits = _section(analysis, "traits")
    trait_reasons = _section(analysis, "trait_reasons")
    subscores = _section(analysis, "subscores")
    fluency = _section(analysis, "fluency")

    return {
        "session_id": session_id,
        "confidence_level": traits.get("confidence_level"),
        "anxiety_level": traits.get("anxiety_level"),
        "clarity_level": traits.get("clarity_level"),
        "focus_level": traits.get("focus_level"),
        "confidence_reasons": _list_value(trait_reasons, "confidence_level"),
        "anxiety_reasons": _list_value(trait_reasons, "anxiety_level"),
        "clarity_reasons": _list_value(trait_reasons, "clarity_level"),
        "focus_reasons": _list_value(trait_reasons, "focus_level"),
        "voice_quality_score": _subscore_value(subscores, "voice_quality", "score"),
        "voice_quality_level": _subscore_value(subscores, "voice_quality", "level"),
        "fluency_score": _subscore_value(subscores, "fluency", "score"),
        "fluency_level": _subscore_value(subscores, "fluency", "level"),
        "energy_control_score": _subscore_value(
            subscores,
            "energy_control",
            "score",
        ),
        "energy_control_level": _subscore_value(
            subscores,
            "energy_control",
            "level",
        ),
        "articulation_score": _subscore_value(subscores, "articulation", "score"),
        "articulation_level": _subscore_value(subscores, "articulation", "level"),
        "words_per_minute": fluency.get("words_per_minute"),
        "pause_ratio": fluency.get("pause_ratio"),
        "filler_word_count": fluency.get("filler_word_count"),
        "pause_count": fluency.get("pause_count"),
        "longest_pause_sec": fluency.get("longest_pause_sec"),
        "confidence_feedback": feedback.get("confidence_feedback", ""),
        "anxiety_feedback": feedback.get("anxiety_feedback", ""),
        "clarity_feedback": feedback.get("clarity_feedback", ""),
        "focus_feedback": feedback.get("focus_feedback", ""),
    }


# used to extract a nested dict from a bigger dict
def _section(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    return value if isinstance(value, dict) else {}


# used to get one value from a nested dict
def _subscore_value(
    subscores: dict[str, Any],
    name: str,
    key: str,
) -> Any:
    subscore = subscores.get(name, {})
    if not isinstance(subscore, dict):
        return None
    return subscore.get(key)


def _list_value(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key, [])
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item]
