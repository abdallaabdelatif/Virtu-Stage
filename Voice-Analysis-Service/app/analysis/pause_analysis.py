# Pause analysis: detects silence segments in the audio to compute
# how much of the session was spent in pauses vs. active speech

from __future__ import annotations
from dataclasses import dataclass
import librosa
import numpy as np

# anything quieter than 30 dB below the peak volume is considered as silence
SILENCE_THRESHOLD_DB = 30
# pauses shorter than this are treated as natural speech gaps not real pauses
MINIMUM_PAUSE_DURATION_SECONDS = 0.5


@dataclass(frozen=True)
class PauseAnalysis:
    pause_ratio: float  # fraction of total audio duration spent in pauses
    pause_count: int  # number of distinct pauses intervals
    longest_pause_seconds: float


class PauseAnalyzer:
    def analyze(self, audio: np.ndarray, sample_rate: int) -> PauseAnalysis:
        total_duration = len(audio) / sample_rate
        if total_duration == 0:
            return PauseAnalysis(
                pause_ratio=0.0, pause_count=0, longest_pause_seconds=0.0
            )

        non_silent_intervals = librosa.effects.split(audio, top_db=SILENCE_THRESHOLD_DB)

        pause_durations = self.gaps_between_intervals(
            non_silent_intervals, sample_rate, total_samples=len(audio)
        )
        real_pauses = [
            d for d in pause_durations if d >= MINIMUM_PAUSE_DURATION_SECONDS
        ]

        total_pause_time = sum(real_pauses)

        return PauseAnalysis(
            pause_ratio=round(total_pause_time / total_duration, 4),
            pause_count=len(real_pauses),
            longest_pause_seconds=round(max(real_pauses, default=0.0), 2),
        )

    # given non-silent [start, end] sample intervals
    # we compute the duration of every gap between them (the pauses)
    @staticmethod
    def gaps_between_intervals(
        intervals: np.ndarray, sample_rate: int, total_samples: int
    ) -> list[float]:
        if len(intervals) == 0:
            return []

        gaps = []
        # Leading silence before the first speech segment
        if intervals[0][0] > 0:
            gaps.append(intervals[0][0] / sample_rate)

        # gaps between consecutive speech segments
        for (_, prev_end), (next_start, _) in zip(intervals, intervals[1:]):
            gap_samples = next_start - prev_end
            if gap_samples > 0:
                gaps.append(gap_samples / sample_rate)

        # trailing silence after the last speech segment
        if intervals[-1][1] < total_samples:
            gaps.append((total_samples - intervals[-1][1]) / sample_rate)
        return gaps
