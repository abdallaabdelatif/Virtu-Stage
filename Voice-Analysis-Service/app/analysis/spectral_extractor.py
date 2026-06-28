from __future__ import annotations
from dataclasses import dataclass, field
import math
import librosa
import numpy as np
from app.analysis.audio_loader import AudioBundle


@dataclass
class SpectralFeatures:
    spectral_centroid_mean: float = field(default=float("nan"))
    spectral_centroid_std: float = field(default=float("nan"))
    spectral_bandwidth_mean: float = field(default=float("nan"))
    spectral_bandwidth_std: float = field(default=float("nan"))
    spectral_rolloff_mean: float = field(default=float("nan"))
    spectral_flatness_mean: float = field(default=float("nan"))
    spectral_contrast_mean: float = field(default=float("nan"))
    zero_crossing_rate_mean: float = field(default=float("nan"))
    spectral_flux_mean: float = field(default=float("nan"))
    spectral_flux_std: float = field(default=float("nan"))
    spectral_entropy_mean: float = field(default=float("nan"))


def extract(bundle: AudioBundle) -> SpectralFeatures:
    result = SpectralFeatures()

    try:
        if bundle.n_samples == 0:
            return result

        hop_length = 512
        n_fft = 2048
        y = np.asarray(bundle.y, dtype=float)

        centroid = librosa.feature.spectral_centroid(
            y=y, sr=bundle.sr, n_fft=n_fft, hop_length=hop_length
        )[0]
        bandwidth = librosa.feature.spectral_bandwidth(
            y=y, sr=bundle.sr, n_fft=n_fft, hop_length=hop_length
        )[0]
        rolloff = librosa.feature.spectral_rolloff(
            y=y, sr=bundle.sr, n_fft=n_fft, hop_length=hop_length
        )[0]
        flatness = librosa.feature.spectral_flatness(
            y=y, n_fft=n_fft, hop_length=hop_length
        )[0]
        contrast = librosa.feature.spectral_contrast(
            y=y, sr=bundle.sr, n_fft=n_fft, hop_length=hop_length
        )
        zcr = librosa.feature.zero_crossing_rate(
            y, frame_length=n_fft, hop_length=hop_length
        )[0]

        result.spectral_centroid_mean = _nanmean(centroid)
        result.spectral_centroid_std = _nanstd(centroid)
        result.spectral_bandwidth_mean = _nanmean(bandwidth)
        result.spectral_bandwidth_std = _nanstd(bandwidth)
        result.spectral_rolloff_mean = _nanmean(rolloff)
        result.spectral_flatness_mean = _nanmean(flatness)
        result.spectral_contrast_mean = _nanmean(contrast)
        result.zero_crossing_rate_mean = _nanmean(zcr)

        magnitude = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length))
        if magnitude.shape[1] >= 2:
            norm = np.linalg.norm(magnitude, axis=0, keepdims=True)
            normalized = magnitude / np.maximum(norm, 1e-10)
            flux = np.sqrt(np.sum(np.diff(normalized, axis=1) ** 2, axis=0))
            result.spectral_flux_mean = _nanmean(flux)
            result.spectral_flux_std = _nanstd(flux)

        power = magnitude**2
        frame_energy = np.sum(power, axis=0, keepdims=True)
        probability = power / np.maximum(frame_energy, 1e-10)
        entropy = -np.sum(probability * np.log2(np.maximum(probability, 1e-10)), axis=0)
        result.spectral_entropy_mean = _nanmean(entropy)
    except Exception:
        pass

    return result


def to_dict(features: SpectralFeatures) -> dict:
    return {
        "spectral_centroid_mean": _safe(features.spectral_centroid_mean),
        "spectral_centroid_std": _safe(features.spectral_centroid_std),
        "spectral_bandwidth_mean": _safe(features.spectral_bandwidth_mean),
        "spectral_bandwidth_std": _safe(features.spectral_bandwidth_std),
        "spectral_rolloff_mean": _safe(features.spectral_rolloff_mean),
        "spectral_flatness_mean": _safe(features.spectral_flatness_mean),
        "spectral_contrast_mean": _safe(features.spectral_contrast_mean),
        "zero_crossing_rate_mean": _safe(features.zero_crossing_rate_mean),
        "spectral_flux_mean": _safe(features.spectral_flux_mean),
        "spectral_flux_std": _safe(features.spectral_flux_std),
        "spectral_entropy_mean": _safe(features.spectral_entropy_mean),
    }


def _nanmean(values) -> float:
    values = np.asarray(values, dtype=float)
    return float(np.nanmean(values)) if values.size else float("nan")


def _nanstd(values) -> float:
    values = np.asarray(values, dtype=float)
    return float(np.nanstd(values)) if values.size else float("nan")


def _safe(value):
    try:
        if value is None:
            return None
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        return value
    except Exception:
        return None
