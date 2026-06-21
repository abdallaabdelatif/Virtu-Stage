# Branch 2: Paralinguistic / acoustic feature analysis
# Treats speech as a pure physical audio signal

from __future__ import annotations
from dataclasses import dataclass
import librosa
import numpy as np


@dataclass(frozen=True)
class ParalinguisticScores:
    anxiety_level: float
    confidence_score: float
    clarity_level: float
    focus_score: float


# Extracts pitch, energy, and jitter-based features and maps them onto normalized 0.0-1.0 scores
# the mapping is heuristic and the thresholds can be changed by experiment or using labeled samples
class ParalinguisticAnalyzer:
    def analyze(self, audio: np.ndarray, sample_rate: int) -> ParalinguisticScores:
        pitch_values = self.extract_pitch_track(audio, sample_rate)
        energy = librosa.feature.rms(y=audio)[0]

        pitch_variability = self.coefficient_of_variation(pitch_values)
        energy_variability = self.coefficient_of_variation(energy)
        mean_energy = float(np.mean(energy)) if len(energy) else 0.0

        anxiety_level = self.normalize(pitch_variability, low=0.05, high=0.4)
        confidence_score = self.normalize(mean_energy, low=0.01, high=0.15)
        clarity_level = 1.0 - self.normalize(energy_variability, low=0.1, high=0.6)
        focus_score = 1.0 - anxiety_level

        return ParalinguisticScores(
            anxiety_level=anxiety_level,
            confidence_score=confidence_score,
            clarity_level=clarity_level,
            focus_score=focus_score,
        )

    @staticmethod
    def extract_pitch_track(audio: np.ndarray, sample_rate: int) -> np.ndarray:
        f0, voiced_flag, _ = librosa.pyin(
            audio,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"),
            sr=sample_rate,
        )
        return f0[voiced_flag] if f0 is not None else np.array([])

    @staticmethod
    def coefficient_of_variation(values: np.ndarray) -> float:
        values = values[~np.isnan(values)] if len(values) else values
        if len(values) == 0 or np.mean(values) == 0:
            return 0.0
        return float(np.std(values) / np.mean(values))

    @staticmethod
    def normalize(value: float, low: float, high: float) -> float:
        if high == low:
            return 0.0
        normalized = (value - low) / (high - low)
        return max(0.0, min(1.0, normalized))
