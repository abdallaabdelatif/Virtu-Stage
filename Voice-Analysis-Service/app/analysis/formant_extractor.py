from __future__ import annotations
from dataclasses import dataclass, field
import math
import numpy as np
from app.analysis.audio_loader import AudioBundle


@dataclass
class FormantFeatures:
    f1_mean_hz: float = field(default=float("nan"))
    f2_mean_hz: float = field(default=float("nan"))
    f3_mean_hz: float = field(default=float("nan"))
    f1_std_hz: float = field(default=float("nan"))
    f2_std_hz: float = field(default=float("nan"))
    f3_std_hz: float = field(default=float("nan"))
    f2_f1_distance_mean_hz: float = field(default=float("nan"))
    formant_stability: float = field(default=float("nan"))


def extract(bundle: AudioBundle) -> FormantFeatures:
    result = FormantFeatures()

    try:
        import parselmouth
        from parselmouth.praat import call

        if bundle.duration <= 0:
            return result

        sound = parselmouth.Sound(bundle.tmp_path)
        formant = call(sound, "To Formant (burg)", 0.01, 5, 5500, 0.025, 50)
        times = np.arange(0.025, bundle.duration, 0.01)

        f1 = _formant_track(formant, 1, times)
        f2 = _formant_track(formant, 2, times)
        f3 = _formant_track(formant, 3, times)

        result.f1_mean_hz = _nanmean(f1)
        result.f2_mean_hz = _nanmean(f2)
        result.f3_mean_hz = _nanmean(f3)
        result.f1_std_hz = _nanstd(f1)
        result.f2_std_hz = _nanstd(f2)
        result.f3_std_hz = _nanstd(f3)

        valid_distance = f2 - f1
        valid_distance = valid_distance[
            np.isfinite(valid_distance) & (valid_distance > 0)
        ]
        result.f2_f1_distance_mean_hz = _nanmean(valid_distance)

        means = np.array(
            [result.f1_mean_hz, result.f2_mean_hz, result.f3_mean_hz], dtype=float
        )
        stds = np.array(
            [result.f1_std_hz, result.f2_std_hz, result.f3_std_hz], dtype=float
        )
        valid = np.isfinite(means) & np.isfinite(stds) & (means > 0)
        if np.any(valid):
            result.formant_stability = float(
                1.0 / (1.0 + np.mean(stds[valid] / means[valid]))
            )
    except Exception:
        pass

    return result


def to_dict(features: FormantFeatures) -> dict:
    return {
        "f1_mean_hz": _safe(features.f1_mean_hz),
        "f2_mean_hz": _safe(features.f2_mean_hz),
        "f3_mean_hz": _safe(features.f3_mean_hz),
        "f1_std_hz": _safe(features.f1_std_hz),
        "f2_std_hz": _safe(features.f2_std_hz),
        "f3_std_hz": _safe(features.f3_std_hz),
        "f2_f1_distance_mean_hz": _safe(features.f2_f1_distance_mean_hz),
        "formant_stability": _safe(features.formant_stability),
    }


def _formant_track(formant, formant_number: int, times: np.ndarray) -> np.ndarray:
    from parselmouth.praat import call

    values = []
    for time in times:
        try:
            value = float(
                call(
                    formant,
                    "Get value at time",
                    formant_number,
                    float(time),
                    "Hertz",
                    "Linear",
                )
            )
        except Exception:
            value = float("nan")
        values.append(value)
    return np.asarray(values, dtype=float)


def _nanmean(values) -> float:
    values = np.asarray(values, dtype=float)
    finite = values[np.isfinite(values)]
    return float(np.mean(finite)) if finite.size else float("nan")


def _nanstd(values) -> float:
    values = np.asarray(values, dtype=float)
    finite = values[np.isfinite(values)]
    return float(np.std(finite)) if finite.size else float("nan")


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
