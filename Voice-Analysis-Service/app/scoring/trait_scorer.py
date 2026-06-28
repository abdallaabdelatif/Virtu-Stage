from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any

from app.scoring.subscores import score_subscores


@dataclass
class TraitResult:
    score: float
    level: str
    reasons: list[str] = field(default_factory=list)
    components: dict[str, float] = field(default_factory=dict)


def score_communication(
    audio: dict[str, Any] | None,
    transcript: dict[str, Any] | None,
) -> dict[str, Any]:
    subscores = score_subscores(audio, transcript)
    risks = _risk_subscores(audio or {}, transcript or {}, subscores)

    traits = {
        "confidence_level": _score_trait(
            "confidence_level",
            subscores,
            {
                "energy_stability": 0.30,
                "voice_quality": 0.25,
                "fluency": 0.20,
                "prosodic_control": 0.15,
                "articulation": 0.10,
            },
            positive=True,
        ),
        "anxiety_level": _score_trait(
            "anxiety_level",
            risks,
            {
                "pitch_instability": 0.30,
                "dysfluency": 0.25,
                "voice_instability": 0.20,
                "energy_instability": 0.15,
                "pace_irregularity": 0.10,
            },
            positive=False,
        ),
        "clarity_level": _score_trait(
            "clarity_level",
            subscores,
            {
                "voice_quality": 0.30,
                "articulation": 0.25,
                "fluency": 0.20,
                "spectral_cleanliness": 0.15,
                "energy_stability": 0.10,
            },
            positive=True,
        ),
        "focus_level": _score_trait(
            "focus_level",
            subscores,
            {
                "fluency": 0.35,
                "energy_stability": 0.25,
                "prosodic_control": 0.20,
                "articulation": 0.10,
                "voice_quality": 0.10,
            },
            positive=True,
        ),
    }

    return {
        "traits": {name: _trait_to_dict(result) for name, result in traits.items()},
        "subscores": subscores,
        "risk_subscores": risks,
    }


def score_final_analysis(
    audio: dict[str, Any] | None,
    transcript: dict[str, Any] | None,
) -> dict[str, Any]:
    scoring = score_communication(audio, transcript)
    fluency = _section(transcript or {}, "fluency")
    subscores = scoring.get("subscores", {})

    return {
        "traits": {
            name: _safe(_num(result, "score"))
            for name, result in scoring.get("traits", {}).items()
        },
        "subscores": {
            "voice_quality": _compact_subscore(subscores.get("voice_quality", {})),
            "fluency": _compact_subscore(subscores.get("fluency", {})),
            "energy_control": _compact_subscore(
                subscores.get("energy_stability", {})
            ),
            "articulation": _compact_subscore(subscores.get("articulation", {})),
        },
        "fluency": {
            "words_per_minute": _safe(_num(fluency, "words_per_minute")),
            "pause_ratio": _safe(_num(fluency, "pause_ratio")),
            "filler_word_count": _safe_int(fluency, "filler_word_count"),
            "pause_count": _safe_int(fluency, "pause_count"),
            "longest_pause_sec": _safe(_num(fluency, "longest_pause_sec")),
        },
    }


def _score_trait(
    trait_name: str,
    source: dict[str, dict[str, Any]],
    weights: dict[str, float],
    positive: bool,
) -> TraitResult:
    total = 0.0
    used_weight = 0.0
    components: dict[str, float] = {}

    for name, weight in weights.items():
        item = source.get(name, {})
        if not item.get("available", False):
            continue
        score = _num(item, "score")
        if score is None:
            continue
        components[name] = round(score, 1)
        total += score * weight
        used_weight += weight

    score = 50.0 if used_weight <= 0 else total / used_weight
    score = round(_clamp(score), 1)

    reasons = _trait_reasons(trait_name, source, weights, positive)
    if not reasons:
        reasons = ["Not enough feature evidence was available to explain this trait."]

    return TraitResult(
        score=score,
        level=_positive_level(score) if positive else _risk_level(score),
        reasons=reasons[:4],
        components=components,
    )


def _risk_subscores(
    audio: dict[str, Any],
    transcript: dict[str, Any],
    subscores: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    pitch = _section(audio, "pitch")
    fluency = _section(transcript, "fluency")

    pitch_risk = _pitch_instability_risk(pitch)
    dysfluency = _inverse_subscore(subscores, "fluency", "Dysfluency risk comes from pauses, fillers, repetitions, and pace.")
    voice_instability = _inverse_subscore(subscores, "voice_quality", "Voice instability risk comes from jitter, shimmer, and harmonic quality.")
    energy_instability = _inverse_subscore(subscores, "energy_stability", "Energy instability risk comes from loudness variation, silence, and emphasis control.")
    pace_irregularity = _pace_irregularity_risk(fluency)

    return {
        "pitch_instability": pitch_risk,
        "dysfluency": dysfluency,
        "voice_instability": voice_instability,
        "energy_instability": energy_instability,
        "pace_irregularity": pace_irregularity,
    }


def _pitch_instability_risk(pitch: dict[str, Any]) -> dict[str, Any]:
    mean_f0 = _num(pitch, "mean_f0_hz")
    std_f0 = _num(pitch, "std_f0_hz")
    f0_cv = std_f0 / mean_f0 if _is_finite(std_f0) and _is_finite(mean_f0) and mean_f0 > 0 else None
    jump_rate = _num(pitch, "semitone_jump_rate")
    perturbation = _num(pitch, "relative_f0_perturbation")
    direction_changes = _num(pitch, "direction_change_rate_per_sec")
    slope = _num(pitch, "slope_hz_per_sec")

    parts = {
        "pitch_variability": _range_score(f0_cv, 0.18, 0.38),
        "pitch_jumps": _range_score(jump_rate, 0.3, 1.5),
        "frame_instability": _range_score(perturbation, 0.04, 0.14),
        "direction_changes": _range_score(direction_changes, 5.0, 16.0),
        "pitch_drift": _range_score(abs(slope) if _is_finite(slope) else None, 8.0, 40.0),
    }
    score, available = _weighted(parts, {
        "pitch_variability": 0.25,
        "pitch_jumps": 0.25,
        "frame_instability": 0.25,
        "direction_changes": 0.15,
        "pitch_drift": 0.10,
    })

    reasons = []
    if _is_finite(jump_rate):
        reasons.append(
            "Large pitch jumps increase anxiety evidence." if jump_rate >= 0.6 else "Pitch jumps do not strongly suggest anxiety."
        )
    if _is_finite(perturbation):
        reasons.append(
            "Frame-to-frame pitch instability is elevated." if perturbation >= 0.07 else "Pitch movement is relatively smooth."
        )

    return _risk_dict(score, available, reasons, {
        "f0_cv": f0_cv,
        "semitone_jump_rate": jump_rate,
        "relative_f0_perturbation": perturbation,
        "direction_change_rate_per_sec": direction_changes,
    })


def _pace_irregularity_risk(fluency: dict[str, Any]) -> dict[str, Any]:
    wpm = _num(fluency, "words_per_minute")
    pause_ratio = _num(fluency, "pause_ratio")
    filler_rate = _num(fluency, "filler_rate_per_minute")
    longest_pause = _num(fluency, "longest_pause_sec")

    if _is_finite(wpm):
        if 115 <= wpm <= 165:
            wpm_risk = 0.0
        elif wpm < 115:
            wpm_risk = _range_score(115 - wpm, 20.0, 70.0)
        else:
            wpm_risk = _range_score(wpm - 165, 20.0, 70.0)
    else:
        wpm_risk = None

    parts = {
        "rate_outside_range": wpm_risk,
        "pause_pressure": _range_score(pause_ratio, 0.18, 0.45),
        "filler_pressure": _range_score(filler_rate, 3.0, 10.0),
        "long_pause_pressure": _range_score(longest_pause, 1.5, 5.0),
    }
    score, available = _weighted(parts, {
        "rate_outside_range": 0.40,
        "pause_pressure": 0.25,
        "filler_pressure": 0.25,
        "long_pause_pressure": 0.10,
    })

    reasons = []
    if _is_finite(wpm):
        reasons.append(
            "Speaking pace is outside the preferred range." if wpm < 115 or wpm > 165 else "Speaking pace is within the preferred range."
        )
    if _is_finite(filler_rate):
        reasons.append(
            "Fillers add pace irregularity." if filler_rate >= 4 else "Filler rate does not strongly disrupt pace."
        )

    return _risk_dict(score, available, reasons, {
        "words_per_minute": wpm,
        "pause_ratio": pause_ratio,
        "filler_rate_per_minute": filler_rate,
        "longest_pause_sec": longest_pause,
    })


def _inverse_subscore(
    subscores: dict[str, dict[str, Any]],
    name: str,
    reason: str,
) -> dict[str, Any]:
    item = subscores.get(name, {})
    score = _num(item, "score")
    available = bool(item.get("available", False)) and score is not None
    risk = 50.0 if score is None else 100.0 - score
    return _risk_dict(risk, available, [reason], item.get("evidence", {}))


def _trait_reasons(
    trait_name: str,
    source: dict[str, dict[str, Any]],
    weights: dict[str, float],
    positive: bool,
) -> list[str]:
    ordered = sorted(weights, key=weights.get, reverse=True)
    reasons: list[str] = []

    for name in ordered:
        item = source.get(name, {})
        if not item.get("available", False):
            continue
        score = _num(item, "score")
        if score is None:
            continue
        label = name.replace("_", " ")
        if positive:
            if score >= 70:
                reasons.append(f"{label.capitalize()} supports this score.")
            elif score < 55:
                reasons.append(f"{label.capitalize()} lowers this score.")
        else:
            if score >= 60:
                reasons.append(f"{label.capitalize()} increases anxiety evidence.")
            elif score < 35:
                reasons.append(f"{label.capitalize()} keeps anxiety evidence low.")

        for reason in item.get("reasons", [])[:1]:
            if reason not in reasons:
                reasons.append(reason)
        if len(reasons) >= 4:
            break

    return reasons


def _risk_dict(
    score: float,
    available: bool,
    reasons: list[str],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    if not available:
        reasons = ["Not enough feature evidence was available for this risk subscore."]
    score = round(_clamp(score), 1)
    return {
        "score": score,
        "level": _risk_level(score),
        "available": available,
        "reasons": reasons[:3],
        "evidence": {key: _safe(value) for key, value in evidence.items()},
    }


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
    if not _is_finite(value) or high <= low:
        return None
    return _clamp((float(value) - low) / (high - low) * 100.0)


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


def _trait_to_dict(result: TraitResult) -> dict[str, Any]:
    return {
        "score": _safe(result.score),
        "level": result.level,
        "reasons": result.reasons,
        "components": result.components,
    }


def _compact_subscore(subscore: dict[str, Any]) -> dict[str, Any]:
    return {
        "score": _safe(_num(subscore, "score")),
        "level": subscore.get("level"),
    }


def _positive_level(score: float) -> str:
    if score >= 80:
        return "high"
    if score >= 60:
        return "moderate_high"
    if score >= 40:
        return "moderate"
    return "low"


def _risk_level(score: float) -> str:
    if score >= 75:
        return "high"
    if score >= 50:
        return "moderate"
    if score >= 25:
        return "low"
    return "very_low"


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


def _safe_int(data: dict[str, Any], key: str) -> int | None:
    value = _num(data, key)
    return int(value) if value is not None else None
