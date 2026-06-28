from __future__ import annotations
from dataclasses import dataclass, field
import math
import re
from typing import Iterable, Optional


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


@dataclass
class FluencyInput:
    transcript: str = ""
    duration_sec: float = 0.0
    pause_count: int = 0
    pause_ratio: float = field(default=float("nan"))
    longest_pause_sec: float = field(default=float("nan"))
    filler_words: Optional[list[str]] = None
    word_timestamps: Optional[list[dict]] = None


@dataclass
class FluencyFeatures:
    words_per_minute: float = field(default=float("nan"))
    characters_per_second: float = field(default=float("nan"))
    pause_ratio: float = field(default=float("nan"))
    pause_count: int = 0
    longest_pause_sec: float = field(default=float("nan"))
    filler_word_count: int = 0
    filler_rate_per_minute: float = field(default=float("nan"))
    filler_ratio: float = field(default=float("nan"))
    repeated_word_count: int = 0
    average_words_per_utterance: float = field(default=float("nan"))


def extract(data: FluencyInput) -> FluencyFeatures:
    result = FluencyFeatures()

    try:
        transcript = data.transcript or ""
        duration = float(data.duration_sec or 0.0)
        words = _tokenize_words(transcript)
        word_count = len(words)

        if duration > 0:
            result.words_per_minute = float(word_count / duration * 60.0)
            result.characters_per_second = float(len(transcript.strip()) / duration)

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
        result.average_words_per_utterance = _average_words_per_utterance(
            transcript, words
        )
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
    word_timestamps: Optional[list[dict]] = None,
) -> FluencyFeatures:
    return extract(
        FluencyInput(
            transcript=transcript,
            duration_sec=duration_sec,
            pause_count=pause_count,
            pause_ratio=pause_ratio,
            longest_pause_sec=longest_pause_sec,
            filler_words=filler_words,
            word_timestamps=word_timestamps,
        )
    )


def to_dict(features: FluencyFeatures) -> dict:
    return {
        "words_per_minute": _safe(features.words_per_minute),
        "characters_per_second": _safe(features.characters_per_second),
        "pause_ratio": _safe(features.pause_ratio),
        "pause_count": features.pause_count,
        "longest_pause_sec": _safe(features.longest_pause_sec),
        "filler_word_count": features.filler_word_count,
        "filler_rate_per_minute": _safe(features.filler_rate_per_minute),
        "filler_ratio": _safe(features.filler_ratio),
        "repeated_word_count": features.repeated_word_count,
        "average_words_per_utterance": _safe(features.average_words_per_utterance),
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


def _average_words_per_utterance(transcript: str, words: list[str]) -> float:
    if not words:
        return 0.0

    utterances = [part for part in re.split(r"[.!?;:\n]+", transcript) if part.strip()]
    if not utterances:
        return float(len(words))

    utterance_word_counts = [
        len(_tokenize_words(utterance)) for utterance in utterances
    ]
    utterance_word_counts = [count for count in utterance_word_counts if count > 0]
    return (
        float(sum(utterance_word_counts) / len(utterance_word_counts))
        if utterance_word_counts
        else 0.0
    )


def _safe(value):
    try:
        if value is None:
            return None
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        return value
    except Exception:
        return None
