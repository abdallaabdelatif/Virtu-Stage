# Transcript-based metrics (filler words + speech rate)


from __future__ import annotations
import re
from dataclasses import dataclass

# Common English filler words/phrases
# matching is case-insensitive
FILLER_WORDS = {
    "um",
    "uh",
    "umm",
    "uhh",
    "like",
    "you know",
    "i mean",
    "actually",
    "basically",
    "literally",
    "so yeah",
    "kind of",
    "sort of",
}


@dataclass(frozen=True)
class TranscriptMetrics:
    filler_word_count: int
    word_count: int
    speech_rate_wpm: float


class TranscriptAnalyzer:
    def analyze(
        self, transcript: str, audio_duration_seconds: float
    ) -> TranscriptMetrics:
        words = self.tokenize(transcript)
        word_count = len(words)

        filler_count = self.count_filler_words(transcript)
        speech_rate_wpm = self.words_per_minute(word_count, audio_duration_seconds)

        return TranscriptMetrics(
            filler_word_count=filler_count,
            word_count=word_count,
            speech_rate_wpm=speech_rate_wpm,
        )

    @staticmethod
    def tokenize(transcript: str) -> list[str]:
        return re.findall(r"\b\w+\b", transcript.lower())

    @staticmethod
    def count_filler_words(transcript: str) -> int:
        text = transcript.lower()
        count = 0
        for filler in FILLER_WORDS:
            pattern = r"\b" + re.escape(filler) + r"\b"
            count += len(re.findall(pattern, text))
        return count

    @staticmethod
    def words_per_minute(word_count: int, duration_seconds: float) -> float:
        if duration_seconds <= 0:
            return 0.0
        minutes = duration_seconds / 60
        return round(word_count / minutes, 2)
