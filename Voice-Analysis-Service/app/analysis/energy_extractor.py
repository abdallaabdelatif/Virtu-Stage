from __future__ import annotations
from dataclasses import dataclass, field
import math
import librosa
import numpy as np
from app.analysis.audio_loader import AudioBundle


@dataclass
class EnergyFeatures:
    rms_mean: float = field(default=float("nan"))
    rms_std: float = field(default=float("nan"))
    rms_range: float = field(default=float("nan"))
    mean_dbfs: float = field(default=float("nan"))
    std_dbfs: float = field(default=float("nan"))
    rms_slope_per_sec: float = field(default=float("nan"))
    energy_rise_rate: float = field(default=float("nan"))
    energy_fall_rate: float = field(default=float("nan"))
    energy_burst_count: int = 0
    silence_ratio: float = field(default=float("nan"))


def extract(bundle: AudioBundle) -> EnergyFeatures:
    result = EnergyFeatures()

    try:
        if bundle.n_samples == 0 or bundle.duration <= 0:
            return result

        hop_length = 512
        rms = librosa.feature.rms(y=bundle.y, frame_length=2048, hop_length=hop_length)[
            0
        ]
        rms = np.asarray(rms, dtype=float)
        rms = rms[np.isfinite(rms)]
        if rms.size == 0:
            return result

        result.rms_mean = float(np.mean(rms))
        result.rms_std = float(np.std(rms))
        result.rms_range = float(np.max(rms) - np.min(rms))

        dbfs = 20.0 * np.log10(np.maximum(rms, 1e-10))
        result.mean_dbfs = float(np.mean(dbfs))
        result.std_dbfs = float(np.std(dbfs))

        times = librosa.frames_to_time(
            np.arange(rms.size), sr=bundle.sr, hop_length=hop_length
        )
        if rms.size >= 2 and not np.allclose(times[0], times[-1]):
            result.rms_slope_per_sec = float(np.polyfit(times, rms, 1)[0])

        diffs = np.diff(rms)
        if diffs.size:
            result.energy_rise_rate = float(np.sum(diffs > 0) / bundle.duration)
            result.energy_fall_rate = float(np.sum(diffs < 0) / bundle.duration)

        burst_threshold = float(np.mean(rms) + 1.5 * np.std(rms))
        is_burst = rms > burst_threshold
        result.energy_burst_count = int(np.sum(is_burst & np.r_[True, ~is_burst[:-1]]))

        silence_threshold = max(float(np.percentile(rms, 20)), result.rms_mean * 0.35)
        result.silence_ratio = float(np.mean(rms <= silence_threshold))
    except Exception:
        pass

    return result


def to_dict(features: EnergyFeatures) -> dict:
    return {
        "rms_mean": _safe(features.rms_mean),
        "rms_std": _safe(features.rms_std),
        "rms_range": _safe(features.rms_range),
        "mean_dbfs": _safe(features.mean_dbfs),
        "std_dbfs": _safe(features.std_dbfs),
        "rms_slope_per_sec": _safe(features.rms_slope_per_sec),
        "energy_rise_rate": _safe(features.energy_rise_rate),
        "energy_fall_rate": _safe(features.energy_fall_rate),
        "energy_burst_count": features.energy_burst_count,
        "silence_ratio": _safe(features.silence_ratio),
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
