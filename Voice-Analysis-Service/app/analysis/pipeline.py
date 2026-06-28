from __future__ import annotations
import asyncio
import logging
import os
import tempfile
from typing import Any, Callable
from app.analysis import audio_loader
from app.analysis import energy_extractor
from app.analysis import fluency_extractor
from app.analysis import formant_extractor
from app.analysis import pitch_extractor
from app.analysis import spectral_extractor
from app.analysis import voice_quality_extractor
from app.audio.audio_buffer import AudioBuffer
from app.audio.transcript_buffer import TranscriptBuffer


logger = logging.getLogger(__name__)


async def analyze_audio_buffer(buffer: AudioBuffer) -> dict[str, Any]:
    return await asyncio.to_thread(_analyze_audio_buffer_sync, buffer)


async def analyze_transcript_buffer(
    buffer: TranscriptBuffer,
    audio_done: asyncio.Event | None = None,
    get_audio_result: Callable[[], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if audio_done is not None and not audio_done.is_set():
        await audio_done.wait()

    duration_sec = 0.0
    pause_metrics = {}
    if get_audio_result is not None:
        audio_result = get_audio_result()
        duration_sec = _audio_duration(audio_result)
        pause_metrics = _section(audio_result, "pause_metrics")

    return await asyncio.to_thread(
        _analyze_transcript_buffer_sync,
        buffer,
        duration_sec,
        pause_metrics,
    )


def _analyze_audio_buffer_sync(buffer: AudioBuffer) -> dict[str, Any]:
    input_path = _write_temp_wav(buffer)
    bundle = None

    try:
        bundle = audio_loader.load_audio(input_path)

        pitch = pitch_extractor.extract(bundle)
        energy = energy_extractor.extract(bundle)
        spectral = spectral_extractor.extract(bundle)
        voice_quality = voice_quality_extractor.extract(bundle)
        formants = formant_extractor.extract(bundle)
        pauses = fluency_extractor.extract_pauses_from_audio(bundle)

        return {
            "audio_info": audio_loader.to_dict(bundle),
            "pitch": pitch_extractor.to_dict(pitch),
            "energy": energy_extractor.to_dict(energy),
            "spectral": spectral_extractor.to_dict(spectral),
            "voice_quality": voice_quality_extractor.to_dict(voice_quality),
            "formants": formant_extractor.to_dict(formants),
            "pause_metrics": fluency_extractor.pauses_to_dict(pauses),
        }
    except Exception as exc:
        logger.exception("Audio analysis failed for session %s", buffer.session_id)
        return {"error": f"audio_analysis_failed: {exc}"}
    finally:
        if bundle is not None:
            audio_loader.cleanup_bundle(bundle)
        _remove_file(input_path)


def _analyze_transcript_buffer_sync(
    buffer: TranscriptBuffer,
    duration_sec: float,
    pause_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    transcript_text = buffer.full_transcript()
    pause_metrics = pause_metrics or {}

    try:
        fluency = fluency_extractor.extract_from_values(
            transcript=transcript_text,
            duration_sec=duration_sec,
            pause_count=_safe_int(pause_metrics, "pause_count"),
            pause_ratio=_safe_float(pause_metrics, "pause_ratio"),
            longest_pause_sec=_safe_float(pause_metrics, "longest_pause_sec"),
        )
        return {
            "transcript": transcript_text,
            "fluency": fluency_extractor.to_dict(fluency),
        }
    except Exception as exc:
        logger.exception("Transcript analysis failed for session %s", buffer.session_id)
        return {
            "transcript": transcript_text,
            "fluency": {},
            "error": f"transcript_analysis_failed: {exc}",
        }


def _write_temp_wav(buffer: AudioBuffer) -> str:
    handle = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    try:
        handle.write(buffer.to_wav_bytes())
        return handle.name
    finally:
        handle.close()


def _audio_duration(audio_result: dict[str, Any]) -> float:
    try:
        return float(audio_result.get("audio_info", {}).get("duration") or 0.0)
    except Exception:
        return 0.0


def _section(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    return value if isinstance(value, dict) else {}


def _safe_float(data: dict[str, Any], key: str) -> float:
    try:
        value = data.get(key)
        if value is None:
            return float("nan")
        return float(value)
    except Exception:
        return float("nan")


def _safe_int(data: dict[str, Any], key: str) -> int:
    try:
        return int(data.get(key) or 0)
    except Exception:
        return 0


def _remove_file(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
