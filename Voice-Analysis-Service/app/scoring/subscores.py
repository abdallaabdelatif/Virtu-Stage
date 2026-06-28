from __future__ import annotations
from dataclasses import dataclass, field
import math
from typing import Any


@dataclass
class SubscoreResult:
    score: float
    level: str
    available: bool
    reasons: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)


def score_subscores(
    audio: dict[str, Any] | None,
    transcript: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    audio = audio or {}
    transcript = transcript or {}

    pitch = _section(audio, "pitch")
    energy = _section(audio, "energy")
    spectral = _section(audio, "spectral")
    voice_quality = _section(audio, "voice_quality")
    formants = _section(audio, "formants")
    fluency = _section(transcript, "fluency")
    audio_info = _section(audio, "audio_info")

    results = {
        "voice_quality": _voice_quality_score(voice_quality),
        "fluency": _fluency_score(fluency),
        "energy_stability": _energy_stability_score(energy, audio_info),
        "prosodic_control": _prosodic_control_score(pitch),
        "articulation": _articulation_score(formants, spectral),
        "spectral_cleanliness": _spectral_cleanliness_score(spectral),
    }
    return {name: _subscore_to_dict(result) for name, result in results.items()}


def _voice_quality_score(features: dict[str, Any]) -> SubscoreResult:
    hnr = _num(features, "hnr_mean_db")
    jitter = _average_values(
        _inverse_range(_num(features, "jitter_local"), 0.008, 0.04),
        _inverse_range(_num(features, "jitter_rap"), 0.004, 0.025),
        _inverse_range(_num(features, "jitter_ppq5"), 0.004, 0.03),
    )
    shimmer = _average_values(
        _inverse_range(_num(features, "shimmer_local"), 0.03, 0.12),
        _inverse_range(_num(features, "shimmer_apq3"), 0.02, 0.08),
        _inverse_range(_num(features, "shimmer_apq5"), 0.025, 0.09),
        _inverse_range(_num(features, "shimmer_local_db"), 0.3, 1.2),
    )
    pulses = _num(features, "n_pulses_detected")

    parts = {
        "harmonic_quality": _range_score(hnr, 5.0, 25.0),
        "pitch_period_stability": jitter,
        "amplitude_stability": shimmer,
        "pulse_reliability": _range_score(pulses, 8.0, 40.0),
    }
    score, available = _weighted(
        parts,
        {
            "harmonic_quality": 0.35,
            "pitch_period_stability": 0.25,
            "amplitude_stability": 0.25,
            "pulse_reliability": 0.15,
        },
    )

    reasons = []
    if _is_finite(hnr):
        reasons.append(
            "Harmonic quality is strong."
            if hnr >= 15
            else "Harmonic quality is limited by breathiness or noise."
        )
    if jitter is not None:
        reasons.append(
            "Pitch periods are stable."
            if jitter >= 70
            else "Pitch-period instability lowers voice stability."
        )
    if shimmer is not None:
        reasons.append(
            "Amplitude cycles are stable."
            if shimmer >= 70
            else "Amplitude instability reduces vocal steadiness."
        )

    return _result(
        score,
        available,
        reasons,
        {
            "hnr_mean_db": hnr,
            "jitter_local": _num(features, "jitter_local"),
            "shimmer_local": _num(features, "shimmer_local"),
            "n_pulses_detected": pulses,
        },
    )


def _fluency_score(features: dict[str, Any]) -> SubscoreResult:
    wpm = _num(features, "words_per_minute")
    pause_ratio = _num(features, "pause_ratio")
    pause_count = _num(features, "pause_count")
    longest_pause = _num(features, "longest_pause_sec")
    filler_rate = _num(features, "filler_rate_per_minute")
    filler_ratio = _num(features, "filler_ratio")
    repeated = _num(features, "repeated_word_count")

    parts = {
        "speaking_rate": _target_range_score(wpm, 90.0, 115.0, 165.0, 200.0),
        "pause_control": _average_values(
            _inverse_range(pause_ratio, 0.08, 0.35),
            _inverse_range(longest_pause, 1.0, 4.0),
            _inverse_range(pause_count, 3.0, 18.0),
        ),
        "filler_control": _average_values(
            _inverse_range(filler_rate, 1.0, 8.0),
            _inverse_range(filler_ratio, 0.02, 0.12),
        ),
        "repetition_control": _inverse_range(repeated, 1.0, 8.0),
    }
    score, available = _weighted(
        parts,
        {
            "speaking_rate": 0.30,
            "pause_control": 0.30,
            "filler_control": 0.25,
            "repetition_control": 0.15,
        },
    )

    reasons = []
    if _is_finite(wpm):
        reasons.append(
            "Speaking rate is in a natural range."
            if 115 <= wpm <= 165
            else "Speaking rate is outside the ideal range."
        )
    if _is_finite(filler_rate):
        reasons.append(
            "Fillers are well controlled."
            if filler_rate <= 3
            else "Frequent fillers reduce fluency."
        )
    if _is_finite(pause_ratio):
        reasons.append(
            "Pauses are controlled."
            if pause_ratio <= 0.18
            else "A high pause ratio interrupts flow."
        )

    return _result(
        score,
        available,
        reasons,
        {
            "words_per_minute": wpm,
            "pause_ratio": pause_ratio,
            "filler_rate_per_minute": filler_rate,
            "filler_ratio": filler_ratio,
            "repeated_word_count": repeated,
        },
    )


def _energy_stability_score(
    features: dict[str, Any],
    audio_info: dict[str, Any],
) -> SubscoreResult:
    mean_dbfs = _num(features, "mean_dbfs")
    std_dbfs = _num(features, "std_dbfs")
    silence_ratio = _num(features, "silence_ratio")
    slope = _num(features, "rms_slope_per_sec")
    bursts = _num(features, "energy_burst_count")
    duration = _num(audio_info, "duration")
    burst_rate = (
        bursts / duration
        if _is_finite(bursts) and _is_finite(duration) and duration > 0
        else None
    )

    parts = {
        "audibility": _target_range_score(mean_dbfs, -42.0, -30.0, -12.0, -6.0),
        "loudness_consistency": _inverse_range(std_dbfs, 4.0, 14.0),
        "silence_control": _inverse_range(silence_ratio, 0.12, 0.45),
        "trend_stability": _inverse_range(
            abs(slope) if _is_finite(slope) else None, 0.0005, 0.006
        ),
        "emphasis_control": _inverse_range(burst_rate, 0.15, 1.2),
    }
    score, available = _weighted(
        parts,
        {
            "audibility": 0.30,
            "loudness_consistency": 0.25,
            "silence_control": 0.20,
            "trend_stability": 0.15,
            "emphasis_control": 0.10,
        },
    )

    reasons = []
    if _is_finite(mean_dbfs):
        reasons.append(
            "Voice level is easy to hear."
            if -30 <= mean_dbfs <= -12
            else "Average loudness is outside the preferred range."
        )
    if _is_finite(std_dbfs):
        reasons.append(
            "Loudness is steady." if std_dbfs <= 7 else "Loudness varies noticeably."
        )
    if _is_finite(silence_ratio):
        reasons.append(
            "Low silence ratio supports steady delivery."
            if silence_ratio <= 0.2
            else "Frequent low-energy frames suggest hesitation."
        )

    return _result(
        score,
        available,
        reasons,
        {
            "mean_dbfs": mean_dbfs,
            "std_dbfs": std_dbfs,
            "silence_ratio": silence_ratio,
            "rms_slope_per_sec": slope,
            "energy_burst_rate": burst_rate,
        },
    )


def _prosodic_control_score(features: dict[str, Any]) -> SubscoreResult:
    mean_f0 = _num(features, "mean_f0_hz")
    std_f0 = _num(features, "std_f0_hz")
    f0_cv = (
        std_f0 / mean_f0
        if _is_finite(std_f0) and _is_finite(mean_f0) and mean_f0 > 0
        else None
    )
    jumps = _num(features, "semitone_jump_rate")
    perturbation = _num(features, "relative_f0_perturbation")
    direction_changes = _num(features, "direction_change_rate_per_sec")
    voiced_ratio = _num(features, "voiced_ratio")
    voiced_prob = _num(features, "mean_voiced_prob")
    slope = _num(features, "slope_hz_per_sec")

    parts = {
        "pitch_variation": _target_range_score(f0_cv, 0.04, 0.08, 0.22, 0.35),
        "jump_control": _inverse_range(jumps, 0.15, 1.2),
        "pitch_smoothness": _inverse_range(perturbation, 0.025, 0.12),
        "direction_control": _inverse_range(direction_changes, 3.0, 14.0),
        "voicing_reliability": _average_values(
            _range_score(voiced_ratio, 0.45, 0.85),
            _range_score(voiced_prob, 0.55, 0.90),
        ),
        "intonation_trend": _inverse_range(
            abs(slope) if _is_finite(slope) else None, 4.0, 35.0
        ),
    }
    score, available = _weighted(
        parts,
        {
            "pitch_variation": 0.25,
            "jump_control": 0.20,
            "pitch_smoothness": 0.20,
            "direction_control": 0.15,
            "voicing_reliability": 0.10,
            "intonation_trend": 0.10,
        },
    )

    reasons = []
    if f0_cv is not None:
        reasons.append(
            "Pitch variation is controlled."
            if 0.08 <= f0_cv <= 0.22
            else "Pitch variation is either too flat or too unstable."
        )
    if _is_finite(jumps):
        reasons.append(
            "Large pitch jumps are rare."
            if jumps <= 0.4
            else "Frequent pitch jumps reduce prosodic control."
        )
    if _is_finite(perturbation):
        reasons.append(
            "Frame-to-frame pitch movement is smooth."
            if perturbation <= 0.05
            else "Frame-to-frame pitch instability is elevated."
        )

    return _result(
        score,
        available,
        reasons,
        {
            "f0_cv": f0_cv,
            "semitone_jump_rate": jumps,
            "relative_f0_perturbation": perturbation,
            "direction_change_rate_per_sec": direction_changes,
            "voiced_ratio": voiced_ratio,
        },
    )


def _articulation_score(
    formants: dict[str, Any],
    spectral: dict[str, Any],
) -> SubscoreResult:
    stability = _num(formants, "formant_stability")
    f2_f1 = _num(formants, "f2_f1_distance_mean_hz")
    contrast = _num(spectral, "spectral_contrast_mean")
    flatness = _num(spectral, "spectral_flatness_mean")
    zcr = _num(spectral, "zero_crossing_rate_mean")
    entropy = _num(spectral, "spectral_entropy_mean")

    parts = {
        "formant_stability": _range_score(stability, 0.82, 0.96),
        "articulation_space": _range_score(f2_f1, 450.0, 1200.0),
        "spectral_contrast": _range_score(contrast, 12.0, 28.0),
        "low_noisiness": _average_values(
            _inverse_range(flatness, 0.015, 0.12),
            _inverse_range(zcr, 0.04, 0.18),
            _inverse_range(entropy, 7.0, 9.5),
        ),
    }
    score, available = _weighted(
        parts,
        {
            "formant_stability": 0.35,
            "articulation_space": 0.25,
            "spectral_contrast": 0.20,
            "low_noisiness": 0.20,
        },
    )

    reasons = []
    if _is_finite(stability):
        reasons.append(
            "Formant contours are stable."
            if stability >= 0.9
            else "Unstable formants may reduce articulation clarity."
        )
    if _is_finite(f2_f1):
        reasons.append(
            "Formant spacing suggests clear vowel shaping."
            if f2_f1 >= 700
            else "Limited F2-F1 spacing suggests a smaller articulation space."
        )
    if _is_finite(contrast):
        reasons.append(
            "Spectral contrast supports articulation richness."
            if contrast >= 18
            else "Low spectral contrast can make speech sound less defined."
        )

    return _result(
        score,
        available,
        reasons,
        {
            "formant_stability": stability,
            "f2_f1_distance_mean_hz": f2_f1,
            "spectral_contrast_mean": contrast,
            "spectral_flatness_mean": flatness,
            "zero_crossing_rate_mean": zcr,
        },
    )


def _spectral_cleanliness_score(features: dict[str, Any]) -> SubscoreResult:
    flatness = _num(features, "spectral_flatness_mean")
    zcr = _num(features, "zero_crossing_rate_mean")
    flux_std = _num(features, "spectral_flux_std")
    entropy = _num(features, "spectral_entropy_mean")
    contrast = _num(features, "spectral_contrast_mean")

    parts = {
        "tonality": _inverse_range(flatness, 0.015, 0.12),
        "low_unvoiced_noise": _inverse_range(zcr, 0.04, 0.18),
        "spectral_stability": _inverse_range(flux_std, 0.03, 0.18),
        "energy_concentration": _inverse_range(entropy, 7.0, 9.5),
        "definition": _range_score(contrast, 12.0, 28.0),
    }
    score, available = _weighted(
        parts,
        {
            "tonality": 0.25,
            "low_unvoiced_noise": 0.20,
            "spectral_stability": 0.20,
            "energy_concentration": 0.20,
            "definition": 0.15,
        },
    )

    reasons = []
    if _is_finite(flatness):
        reasons.append(
            "The spectrum is mostly tonal."
            if flatness <= 0.04
            else "Higher flatness suggests more noise or breathiness."
        )
    if _is_finite(zcr):
        reasons.append(
            "Unvoiced/noisy activity is controlled."
            if zcr <= 0.08
            else "Zero-crossing rate suggests extra noisy activity."
        )
    if _is_finite(flux_std):
        reasons.append(
            "Spectral changes are stable."
            if flux_std <= 0.08
            else "Spectral changes fluctuate noticeably."
        )

    return _result(
        score,
        available,
        reasons,
        {
            "spectral_flatness_mean": flatness,
            "zero_crossing_rate_mean": zcr,
            "spectral_flux_std": flux_std,
            "spectral_entropy_mean": entropy,
            "spectral_contrast_mean": contrast,
        },
    )


def _section(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    return value if isinstance(value, dict) else {}


def _num(data: dict[str, Any], key: str) -> float | None:
    try:
        value = data.get(key)
        if value is None:
            return None
        value = float(value)
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    except Exception:
        return None


def _range_score(value: float | None, low: float, high: float) -> float | None:
    if not _is_finite(value):
        return None
    if high <= low:
        return None
    return _clamp((float(value) - low) / (high - low) * 100.0)


def _inverse_range(value: float | None, good: float, poor: float) -> float | None:
    if not _is_finite(value):
        return None
    if poor <= good:
        return None
    return _clamp(100.0 - ((float(value) - good) / (poor - good) * 100.0))


def _target_range_score(
    value: float | None,
    outer_low: float,
    inner_low: float,
    inner_high: float,
    outer_high: float,
) -> float | None:
    if not _is_finite(value):
        return None
    value = float(value)
    if inner_low <= value <= inner_high:
        return 100.0
    if value < inner_low:
        return _clamp((value - outer_low) / (inner_low - outer_low) * 100.0)
    return _clamp((outer_high - value) / (outer_high - inner_high) * 100.0)


def _average_values(*values: float | None) -> float | None:
    finite = [float(value) for value in values if _is_finite(value)]
    if not finite:
        return None
    return sum(finite) / len(finite)


def _weighted(
    parts: dict[str, float | None],
    weights: dict[str, float],
) -> tuple[float, bool]:
    total = 0.0
    used_weight = 0.0
    for key, value in parts.items():
        if not _is_finite(value):
            continue
        weight = float(weights.get(key, 0.0))
        total += float(value) * weight
        used_weight += weight
    if used_weight <= 0:
        return 50.0, False
    return _clamp(total / used_weight), True


def _result(
    score: float,
    available: bool,
    reasons: list[str],
    evidence: dict[str, Any],
) -> SubscoreResult:
    if not available:
        reasons = ["Not enough feature evidence was available for this subscore."]
    return SubscoreResult(
        score=round(float(score), 1),
        level=_level(score),
        available=available,
        reasons=reasons[:3],
        evidence={key: _safe(value) for key, value in evidence.items()},
    )


def _subscore_to_dict(result: SubscoreResult) -> dict[str, Any]:
    return {
        "score": _safe(result.score),
        "level": result.level,
        "available": result.available,
        "reasons": result.reasons,
        "evidence": result.evidence,
    }


def _level(score: float) -> str:
    if score >= 80:
        return "strong"
    if score >= 60:
        return "good"
    if score >= 40:
        return "fair"
    return "needs_attention"


def _is_finite(value: Any) -> bool:
    try:
        return value is not None and math.isfinite(float(value))
    except Exception:
        return False


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def _safe(value: Any) -> Any:
    try:
        if value is None:
            return None
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        return value
    except Exception:
        return None
