from __future__ import annotations
from dataclasses import dataclass, field
import math
import re
from typing import Iterable, Optional
import numpy as np
from app.analysis.audio_loader import AudioBundle


FILLER_WORDS = {
    "um",
    "uh",
    "erm",
    "hmm",
    "like",
    "actually",
    "basically",
    "literally",
    "you know",
    "i mean",
}

PAUSE_DB_MARGIN = 10.0
MIN_PAUSE_SEC = 0.5


@dataclass
class FluencyInput:
    transcript: str = ""
    duration_sec: float = 0.0
    pause_count: int = 0
    pause_ratio: float = field(default=float("nan"))
    longest_pause_sec: float = field(default=float("nan"))
    filler_words: Optional[list[str]] = None


@dataclass
class FluencyFeatures:
    words_per_minute: float = field(default=float("nan"))
    pause_ratio: float = field(default=float("nan"))
    pause_count: int = 0
    longest_pause_sec: float = field(default=float("nan"))
    filler_word_count: int = 0
    filler_rate_per_minute: float = field(default=float("nan"))
    filler_ratio: float = field(default=float("nan"))
    repeated_word_count: int = 0


@dataclass
class PauseFeatures:
    pause_ratio: float = field(default=float("nan"))
    pause_count: int = 0
    longest_pause_sec: float = field(default=float("nan"))


def extract(data: FluencyInput) -> FluencyFeatures:
    result = FluencyFeatures()

    try:
        transcript = data.transcript or ""
        duration = float(data.duration_sec or 0.0)
        words = _tokenize_words(transcript)
        word_count = len(words)

        if duration > 0:
            result.words_per_minute = float(word_count / duration * 60.0)

        result.pause_ratio = data.pause_ratio
        result.pause_count = int(data.pause_count or 0)
        result.longest_pause_sec = data.longest_pause_sec

        result.filler_word_count = _count_fillers(transcript, data.filler_words)
        if duration > 0:
            result.filler_rate_per_minute = float(
                result.filler_word_count / duration * 60.0
            )
        result.filler_ratio = (
            float(result.filler_word_count / word_count) if word_count else 0.0
        )

        result.repeated_word_count = _count_repeated_words(words)
    except Exception:
        pass

    return result


def extract_from_values(
    transcript: str,
    duration_sec: float,
    pause_count: int = 0,
    pause_ratio: float = float("nan"),
    longest_pause_sec: float = float("nan"),
    filler_words: Optional[list[str]] = None,
) -> FluencyFeatures:
    return extract(
        FluencyInput(
            transcript=transcript,
            duration_sec=duration_sec,
            pause_count=pause_count,
            pause_ratio=pause_ratio,
            longest_pause_sec=longest_pause_sec,
            filler_words=filler_words,
        )
    )


def extract_pauses_from_audio(bundle: AudioBundle) -> PauseFeatures:
    result = PauseFeatures()

    try:
        if bundle.n_samples == 0 or bundle.duration <= 0:
            return result

        frame_length = 2048
        hop_length = 512
        rms = _frame_rms(bundle.y, frame_length, hop_length)
        if rms.size == 0:
            return result

        rms_floor = np.maximum(rms, 1e-10)
        db = 20.0 * np.log10(rms_floor / np.max(rms_floor))
        speech_threshold_db = max(
            float(np.percentile(db, 20)),
            float(np.median(db) - PAUSE_DB_MARGIN),
        )
        silent_frames = db <= speech_threshold_db
        frame_duration = float(hop_length / bundle.sr)
        min_pause_frames = max(1, int(round(MIN_PAUSE_SEC / frame_duration)))

        pauses = _silent_runs_to_durations(
            silent_frames,
            frame_duration,
            min_pause_frames,
        )
        result.pause_count = len(pauses)
        result.longest_pause_sec = float(max(pauses)) if pauses else 0.0
        result.pause_ratio = (
            float(sum(pauses) / bundle.duration)
            if bundle.duration > 0
            else float("nan")
        )
    except Exception:
        pass

    return result


def to_dict(features: FluencyFeatures) -> dict:
    return {
        "words_per_minute": _safe(features.words_per_minute),
        "pause_ratio": _safe(features.pause_ratio),
        "pause_count": features.pause_count,
        "longest_pause_sec": _safe(features.longest_pause_sec),
        "filler_word_count": features.filler_word_count,
        "filler_rate_per_minute": _safe(features.filler_rate_per_minute),
        "filler_ratio": _safe(features.filler_ratio),
        "repeated_word_count": features.repeated_word_count,
    }


def pauses_to_dict(features: PauseFeatures) -> dict:
    return {
        "pause_ratio": _safe(features.pause_ratio),
        "pause_count": features.pause_count,
        "longest_pause_sec": _safe(features.longest_pause_sec),
    }


def _tokenize_words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z']+", text.lower())


def _count_fillers(transcript: str, filler_words: Optional[Iterable[str]]) -> int:
    words = set(filler_words or FILLER_WORDS)
    text = transcript.lower()
    count = 0

    for filler in words:
        pattern = r"\b" + re.escape(filler.lower()) + r"\b"
        count += len(re.findall(pattern, text))

    return count


def _count_repeated_words(words: list[str]) -> int:
    if len(words) < 2:
        return 0
    return int(
        sum(
            1 for current, previous in zip(words[1:], words[:-1]) if current == previous
        )
    )


def _silent_runs_to_durations(
    silent_frames: np.ndarray,
    frame_duration: float,
    min_pause_frames: int,
) -> list[float]:
    pauses = []
    run_length = 0

    for is_silent in silent_frames:
        if bool(is_silent):
            run_length += 1
            continue

        if run_length >= min_pause_frames:
            pauses.append(float(run_length * frame_duration))
        run_length = 0

    if run_length >= min_pause_frames:
        pauses.append(float(run_length * frame_duration))

    return pauses


def _frame_rms(y: np.ndarray, frame_length: int, hop_length: int) -> np.ndarray:
    if y.size == 0 or frame_length <= 0 or hop_length <= 0:
        return np.asarray([], dtype=float)

    if y.size < frame_length:
        frame = np.pad(y, (0, frame_length - y.size))
        return np.asarray([float(np.sqrt(np.mean(np.square(frame))))])

    starts = range(0, y.size - frame_length + 1, hop_length)
    values = [
        float(np.sqrt(np.mean(np.square(y[start : start + frame_length]))))
        for start in starts
    ]
    return np.asarray(values, dtype=float)


def _safe(value):
    try:
        if value is None:
            return None
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        return value
    except Exception:
        return None
