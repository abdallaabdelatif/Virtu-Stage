from __future__ import annotations
from dataclasses import dataclass, field
import math
import os
import tempfile
from typing import Optional
import librosa
import numpy as np
import soundfile as sf


TARGET_SAMPLE_RATE = 16000


@dataclass
class AudioBundle:
    y: np.ndarray
    sr: int
    duration: float
    n_samples: int
    tmp_path: str
    original_sr: int
    n_channels: int
    rms_global: float = field(default=float("nan"))


def load_audio(path: str, target_sr: int = TARGET_SAMPLE_RATE) -> AudioBundle:
    data, original_sr = sf.read(path, always_2d=True, dtype="float32")
    n_channels = int(data.shape[1]) if data.ndim == 2 else 1

    if data.ndim == 2:
        y = np.mean(data, axis=1)
    else:
        y = data

    y = np.asarray(y, dtype=np.float32)

    if original_sr != target_sr:
        y = librosa.resample(y, orig_sr=original_sr, target_sr=target_sr)
        y = np.asarray(y, dtype=np.float32)

    n_samples = int(len(y))
    duration = float(n_samples / target_sr) if target_sr > 0 else 0.0
    rms_global = float(np.sqrt(np.mean(np.square(y)))) if n_samples else float("nan")
    tmp_path = _write_temp_wav(y, target_sr)

    return AudioBundle(
        y=y,
        sr=int(target_sr),
        duration=duration,
        n_samples=n_samples,
        tmp_path=tmp_path,
        original_sr=int(original_sr),
        n_channels=n_channels,
        rms_global=rms_global,
    )


def cleanup_bundle(bundle: AudioBundle) -> None:
    try:
        if bundle.tmp_path and os.path.exists(bundle.tmp_path):
            os.remove(bundle.tmp_path)
    except Exception:
        pass


def to_dict(bundle: AudioBundle) -> dict:
    return {
        "sample_rate": bundle.sr,
        "duration": _safe(bundle.duration),
        "n_samples": bundle.n_samples,
        "original_sr": bundle.original_sr,
        "n_channels": bundle.n_channels,
        "rms_global": _safe(bundle.rms_global),
    }


def _write_temp_wav(y: np.ndarray, sr: int) -> str:
    handle = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp_path = handle.name
    handle.close()
    sf.write(tmp_path, y, sr)
    return tmp_path


def _safe(value: Optional[float]):
    try:
        if value is None:
            return None
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        return value
    except Exception:
        return None
