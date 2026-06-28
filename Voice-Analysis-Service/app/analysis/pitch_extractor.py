from __future__ import annotations
from dataclasses import dataclass, field
import math
import librosa
import numpy as np
from app.analysis.audio_loader import AudioBundle


@dataclass
class PitchFeatures:
    mean_f0_hz: float = field(default=float("nan"))
    median_f0_hz: float = field(default=float("nan"))
    std_f0_hz: float = field(default=float("nan"))
    range_f0_hz: float = field(default=float("nan"))
    slope_hz_per_sec: float = field(default=float("nan"))
    voiced_ratio: float = field(default=float("nan"))
    mean_voiced_prob: float = field(default=float("nan"))
    rising_fraction: float = field(default=float("nan"))
    falling_fraction: float = field(default=float("nan"))
    direction_change_rate_per_sec: float = field(default=float("nan"))
    semitone_jump_rate: float = field(default=float("nan"))
    relative_f0_perturbation: float = field(default=float("nan"))


def extract(bundle: AudioBundle) -> PitchFeatures:
    result = PitchFeatures()

    try:
        if bundle.n_samples == 0 or bundle.duration <= 0:
            return result

        f0, voiced_flag, voiced_prob = librosa.pyin(
            bundle.y,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"),
            sr=bundle.sr,
            frame_length=2048,
            hop_length=512,
        )

        voiced_flag = np.asarray(voiced_flag, dtype=bool)
        voiced_prob = np.asarray(voiced_prob, dtype=float)
        voiced_f0 = np.asarray(f0, dtype=float)[voiced_flag & np.isfinite(f0)]

        result.voiced_ratio = (
            float(np.mean(voiced_flag)) if voiced_flag.size else float("nan")
        )
        result.mean_voiced_prob = (
            float(np.nanmean(voiced_prob)) if voiced_prob.size else float("nan")
        )

        if voiced_f0.size < 2:
            if voiced_f0.size == 1:
                result.mean_f0_hz = float(voiced_f0[0])
                result.median_f0_hz = float(voiced_f0[0])
                result.std_f0_hz = 0.0
                result.range_f0_hz = 0.0
            return result

        result.mean_f0_hz = float(np.mean(voiced_f0))
        result.median_f0_hz = float(np.median(voiced_f0))
        result.std_f0_hz = float(np.std(voiced_f0))
        result.range_f0_hz = float(np.max(voiced_f0) - np.min(voiced_f0))

        voiced_indices = np.flatnonzero(voiced_flag & np.isfinite(f0))
        times = librosa.frames_to_time(voiced_indices, sr=bundle.sr, hop_length=512)
        if len(times) >= 2 and not np.allclose(times[0], times[-1]):
            result.slope_hz_per_sec = float(np.polyfit(times, voiced_f0, 1)[0])

        diffs = np.diff(voiced_f0)
        nonzero_diffs = diffs[np.abs(diffs) > 1e-6]
        if diffs.size:
            result.rising_fraction = float(np.mean(diffs > 0))
            result.falling_fraction = float(np.mean(diffs < 0))
            result.relative_f0_perturbation = float(
                np.mean(np.abs(diffs)) / max(result.mean_f0_hz, 1e-9)
            )

        if nonzero_diffs.size >= 2:
            signs = np.sign(nonzero_diffs)
            direction_changes = int(np.sum(signs[1:] != signs[:-1]))
            result.direction_change_rate_per_sec = float(
                direction_changes / bundle.duration
            )

        semitone_steps = np.abs(12.0 * np.log2(voiced_f0[1:] / voiced_f0[:-1]))
        result.semitone_jump_rate = float(
            np.sum(semitone_steps >= 3.0) / bundle.duration
        )
    except Exception:
        pass

    return result


def to_dict(features: PitchFeatures) -> dict:
    return {
        "mean_f0_hz": _safe(features.mean_f0_hz),
        "median_f0_hz": _safe(features.median_f0_hz),
        "std_f0_hz": _safe(features.std_f0_hz),
        "range_f0_hz": _safe(features.range_f0_hz),
        "slope_hz_per_sec": _safe(features.slope_hz_per_sec),
        "voiced_ratio": _safe(features.voiced_ratio),
        "mean_voiced_prob": _safe(features.mean_voiced_prob),
        "rising_fraction": _safe(features.rising_fraction),
        "falling_fraction": _safe(features.falling_fraction),
        "direction_change_rate_per_sec": _safe(features.direction_change_rate_per_sec),
        "semitone_jump_rate": _safe(features.semitone_jump_rate),
        "relative_f0_perturbation": _safe(features.relative_f0_perturbation),
    }


def _safe(value):
    try:
        if value is None:
            return None
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        return value
    except Exception:
        return None
