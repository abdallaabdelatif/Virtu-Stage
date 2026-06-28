from __future__ import annotations
from dataclasses import dataclass, field
import math
import numpy as np
from app.analysis.audio_loader import AudioBundle


@dataclass
class VoiceQualityFeatures:
    jitter_local: float = field(default=float("nan"))
    jitter_local_abs: float = field(default=float("nan"))
    jitter_rap: float = field(default=float("nan"))
    jitter_ppq5: float = field(default=float("nan"))
    shimmer_local: float = field(default=float("nan"))
    shimmer_local_db: float = field(default=float("nan"))
    shimmer_apq3: float = field(default=float("nan"))
    shimmer_apq5: float = field(default=float("nan"))
    hnr_mean_db: float = field(default=float("nan"))
    n_pulses_detected: int = 0


def extract(bundle: AudioBundle) -> VoiceQualityFeatures:
    result = VoiceQualityFeatures()

    try:
        import parselmouth
        from parselmouth.praat import call

        if bundle.duration <= 0:
            return result

        sound = parselmouth.Sound(bundle.tmp_path)
        pitch_floor = 75.0
        pitch_ceiling = 500.0
        point_process = call(
            sound, "To PointProcess (periodic, cc)", pitch_floor, pitch_ceiling
        )
        result.n_pulses_detected = int(call(point_process, "Get number of points"))

        if result.n_pulses_detected >= 2:
            result.jitter_local = _call_float(
                point_process,
                "Get jitter (local)",
                0,
                0,
                0.0001,
                0.02,
                1.3,
            )
            result.jitter_local_abs = _call_float(
                point_process,
                "Get jitter (local, absolute)",
                0,
                0,
                0.0001,
                0.02,
                1.3,
            )
            result.jitter_rap = _call_float(
                point_process,
                "Get jitter (rap)",
                0,
                0,
                0.0001,
                0.02,
                1.3,
            )
            result.jitter_ppq5 = _call_float(
                point_process,
                "Get jitter (ppq5)",
                0,
                0,
                0.0001,
                0.02,
                1.3,
            )

        if result.n_pulses_detected >= 3:
            result.shimmer_local = _call_float(
                [sound, point_process],
                "Get shimmer (local)",
                0,
                0,
                0.0001,
                0.02,
                1.3,
                1.6,
            )
            result.shimmer_local_db = _call_float(
                [sound, point_process],
                "Get shimmer (local_dB)",
                0,
                0,
                0.0001,
                0.02,
                1.3,
                1.6,
            )
            result.shimmer_apq3 = _call_float(
                [sound, point_process],
                "Get shimmer (apq3)",
                0,
                0,
                0.0001,
                0.02,
                1.3,
                1.6,
            )
            result.shimmer_apq5 = _call_float(
                [sound, point_process],
                "Get shimmer (apq5)",
                0,
                0,
                0.0001,
                0.02,
                1.3,
                1.6,
            )

        harmonicity = call(sound, "To Harmonicity (cc)", 0.01, pitch_floor, 0.1, 1.0)
        result.hnr_mean_db = _call_float(harmonicity, "Get mean", 0, 0)
    except Exception:
        pass

    return result


def to_dict(features: VoiceQualityFeatures) -> dict:
    return {
        "jitter_local": _safe(features.jitter_local),
        "jitter_local_abs": _safe(features.jitter_local_abs),
        "jitter_rap": _safe(features.jitter_rap),
        "jitter_ppq5": _safe(features.jitter_ppq5),
        "shimmer_local": _safe(features.shimmer_local),
        "shimmer_local_db": _safe(features.shimmer_local_db),
        "shimmer_apq3": _safe(features.shimmer_apq3),
        "shimmer_apq5": _safe(features.shimmer_apq5),
        "hnr_mean_db": _safe(features.hnr_mean_db),
        "n_pulses_detected": features.n_pulses_detected,
    }


def _call_float(obj, command: str, *args) -> float:
    from parselmouth.praat import call

    value = call(obj, command, *args)
    return float(value)


def _safe(value):
    try:
        if value is None:
            return None
        if isinstance(value, (float, np.floating)) and (
            math.isnan(float(value)) or math.isinf(float(value))
        ):
            return None
        return value
    except Exception:
        return None
