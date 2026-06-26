# this file is responsible for coordination between the two analysis branches
# each branch stars once its socket is closed except if the audio duration is not ready yet, the transcript
# analysis has to wait till audio duration is available
from __future__ import annotations
import asyncio
import logging
from dataclasses import dataclass, field
from app.analysis.pipeline import AudioAnalysisPipeline, TranscriptAnalysisPipeline
from app.audio.audio_buffer import AudioBuffer
from app.audio.transcript_buffer import TranscriptBuffer
from app.schemas.result import VoiceAnalysisResult
from app.websocket.result_sender import send_result_to_central_backend
from app.websocket.session_registry import session_registry

logger = logging.getLogger(__name__)

# the model is loaded once at import time and reused across all sessions
audio_pipeline = AudioAnalysisPipeline()
transcript_pipeline = TranscriptAnalysisPipeline()


@dataclass
class SessionSync:
    audio_duration_ready: asyncio.Event = field(default_factory=asyncio.Event)
    audio_done: asyncio.Event = field(default_factory=asyncio.Event)
    transcript_done: asyncio.Event = field(default_factory=asyncio.Event)
    audio_duration_seconds: float = 0.0


session_sync: dict[str, SessionSync] = {}


def get_sync(session_id: str) -> SessionSync:
    if session_id not in session_sync:
        session_sync[session_id] = SessionSync()
    return session_sync[session_id]


# triggered when the audio socket is closed(session ends), runs the audio analysis part
async def on_audio_socket_closed(session_id: str, audio_buffer: AudioBuffer) -> None:
    sync = get_sync(session_id)
    state = session_registry.get_or_create(session_id)

    if audio_buffer.has_audio:
        try:
            result = await audio_pipeline.run(session_id, audio_buffer)
            state.audio_result = result
            sync.audio_duration_seconds = result.duration_seconds
        except Exception:
            logger.exception("Audio analysis failed for session %s", session_id)
    else:
        logger.warning(
            "Session %s: audio socket closed with no audio received", session_id
        )

    # unblocks transcript analysis if it is waiting on duration
    sync.audio_duration_ready.set()
    sync.audio_done.set()
    await merge_and_send(session_id)


async def on_transcript_socket_closed(
    session_id: str, transcript_buffer: TranscriptBuffer
) -> None:
    sync = get_sync(session_id)
    state = session_registry.get_or_create(session_id)

    if transcript_buffer.has_text:
        await (
            sync.audio_duration_ready.wait()
        )  # wait till the flag is set (audio duration available)
        try:
            result = transcript_pipeline.run(
                session_id, transcript_buffer, sync.audio_duration_seconds
            )
            state.transcript_result = result
        except Exception:
            logger.exception("Transcript analysis failed for session %s", session_id)
    else:
        logger.warning(
            "Session %s: transcript socket closed with no text received", session_id
        )

    sync.transcript_done.set()
    await merge_and_send(session_id)


async def merge_and_send(session_id: str) -> None:
    sync = get_sync(session_id)

    # when one analysis branch finishes it sets its flag true
    # merge and send results only when both are ready
    if not (sync.audio_done.is_set() and sync.transcript_done.is_set()):
        return

    state = session_registry.get_or_create(session_id)

    if not state.both_results_ready:
        logger.warning("Session %s: Analysis failed", session_id)
        cleanup(session_id)
        return

    logger.info(
        "Both analysis results are ready for session %s, merging and sending",
        session_id,
    )

    merged = VoiceAnalysisResult(
        session_id=session_id,
        emotions=state.audio_result.emotions,
        paralinguistic=state.audio_result.paralinguistic,
        pauses=state.audio_result.pauses,
        filler_word_count=state.transcript_result.filler_word_count,
        speech_rate_wpm=state.transcript_result.speech_rate_wpm,
    )

    await send_result_to_central_backend(merged)
    cleanup(session_id)


def cleanup(session_id: str) -> None:
    session_registry.remove(session_id)
    session_sync.pop(session_id, None)
