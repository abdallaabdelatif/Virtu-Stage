from __future__ import annotations

from typing import Any

from app.scoring import trait_scorer


TRAIT_LABELS = {
    "confidence_level": "Confidence",
    "anxiety_level": "Anxiety",
    "clarity_level": "Clarity",
    "focus_level": "Focus",
}

FACTOR_LABELS = {
    "energy_stability": "loudness control",
    "voice_quality": "voice stability",
    "fluency": "fluency",
    "prosodic_control": "pitch control",
    "articulation": "articulation",
    "spectral_cleanliness": "vocal cleanliness",
    "pitch_instability": "pitch instability",
    "dysfluency": "pauses and fillers",
    "voice_instability": "voice instability",
    "energy_instability": "loudness instability",
    "pace_irregularity": "pace irregularity",
}

CALMING_FACTOR_LABELS = {
    "pitch_instability": "stable pitch movement",
    "dysfluency": "controlled pauses and fillers",
    "voice_instability": "steady voice quality",
    "energy_instability": "steady loudness",
    "pace_irregularity": "controlled pace",
}

TRAIT_FACTOR_PRIORITY = {
    "confidence_level": [
        "energy_stability",
        "voice_quality",
        "fluency",
        "prosodic_control",
        "articulation",
    ],
    "clarity_level": [
        "voice_quality",
        "articulation",
        "spectral_cleanliness",
        "fluency",
        "energy_stability",
    ],
    "focus_level": [
        "fluency",
        "energy_stability",
        "prosodic_control",
        "articulation",
        "voice_quality",
    ],
    "anxiety_level": [
        "pitch_instability",
        "dysfluency",
        "voice_instability",
        "energy_instability",
        "pace_irregularity",
    ],
}


def build_trait_feedback(
    audio: dict[str, Any] | None,
    transcript: dict[str, Any] | None,
) -> dict[str, str]:
    scoring = trait_scorer.score_communication(audio, transcript)
    traits = scoring.get("traits", {})

    return {
        "confidence_feedback": _sentence(
            "confidence_level",
            traits.get("confidence_level", {}),
        ),
        "anxiety_feedback": _sentence(
            "anxiety_level",
            traits.get("anxiety_level", {}),
        ),
        "clarity_feedback": _sentence(
            "clarity_level",
            traits.get("clarity_level", {}),
        ),
        "focus_feedback": _sentence(
            "focus_level",
            traits.get("focus_level", {}),
        ),
    }


def _sentence(trait_name: str, trait: dict[str, Any]) -> str:
    label = TRAIT_LABELS.get(trait_name, trait_name.replace("_", " ").title())
    score = _score_text(trait.get("score"))
    level = str(trait.get("level") or "moderate").replace("_", " ")
    components = _components(trait)

    strengths = _factor_names(
        _ordered_factors(trait_name, components, high=True),
        FACTOR_LABELS,
    )
    limiters = _factor_names(
        _ordered_factors(trait_name, components, high=False),
        FACTOR_LABELS,
    )

    if trait_name == "anxiety_level":
        contributors = _factor_names(
            _ordered_factors(trait_name, components, high=True),
            FACTOR_LABELS,
        )
        calming = _factor_names(
            _ordered_factors(trait_name, components, high=False),
            CALMING_FACTOR_LABELS,
        )
        lead = f"{label} evidence is {level} ({score})."
        if contributors and calming:
            return f"{lead} Main contributors: {contributors}; calming factors: {calming}."
        if contributors:
            return f"{lead} Main contributors: {contributors}."
        if calming:
            return f"{lead} Calming factors: {calming}."
        return f"{lead} {_first_reason(trait)}"

    lead = f"{label} is {level} ({score})."
    if strengths and limiters:
        return f"{lead} Strengths: {strengths}; watch: {limiters}."
    if strengths:
        return f"{lead} Strong contributors: {strengths}."
    if limiters:
        return f"{lead} Main areas to improve: {limiters}."
    return f"{lead} {_first_reason(trait)}"


def _components(trait: dict[str, Any]) -> dict[str, float]:
    raw_components = trait.get("components", {})
    if not isinstance(raw_components, dict):
        return {}

    components: dict[str, float] = {}
    for name, value in raw_components.items():
        try:
            components[name] = float(value)
        except Exception:
            continue
    return components


def _ordered_factors(
    trait_name: str,
    components: dict[str, float],
    high: bool,
) -> list[str]:
    selected = []
    for name, value in components.items():
        if high and _is_high(value):
            selected.append(name)
        elif not high and _is_low(value):
            selected.append(name)
    priority = TRAIT_FACTOR_PRIORITY.get(trait_name, list(components))
    selected.sort(key=lambda name: priority.index(name) if name in priority else 999)
    return selected[:2]


def _factor_names(names: Any, labels_by_name: dict[str, str]) -> str:
    labels = [
        labels_by_name.get(name, FACTOR_LABELS.get(name, name.replace("_", " ")))
        for name in names
    ]
    if not labels:
        return ""
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]} and {labels[1]}"
    return ", ".join(labels[:-1]) + f", and {labels[-1]}"


def _score_text(score: Any) -> str:
    try:
        return f"{round(float(score), 1)}/100"
    except Exception:
        return "not enough evidence"


def _first_reason(trait: dict[str, Any]) -> str:
    reasons = trait.get("reasons", [])
    if isinstance(reasons, list) and reasons:
        return str(reasons[0])
    return "More evidence is needed for a detailed explanation."


def _is_high(value: float) -> bool:
    return value >= 70.0


def _is_low(value: float) -> bool:
    return value < 55.0
