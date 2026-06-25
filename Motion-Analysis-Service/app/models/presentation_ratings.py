from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from app.models.motion_metrics import MotionMetrics


class PresentationRating(str, Enum):
    """Categorical delivery quality aligned with MIT CommLab nonverbal guidance."""

    EXCELLENT = "excellent"
    GOOD = "good"
    DEVELOPING = "developing"
    NEEDS_WORK = "needs_work"


RATING_SEVERITY = {
    PresentationRating.EXCELLENT: 0,
    PresentationRating.GOOD: 1,
    PresentationRating.DEVELOPING: 2,
    PresentationRating.NEEDS_WORK: 3,
}

RATING_DESCRIPTIONS: dict[str, str] = {
    PresentationRating.EXCELLENT.value: (
        "Strong nonverbal delivery: upright posture, steady gaze, purposeful gestures, "
        "and minimal distracting movement."
    ),
    PresentationRating.GOOD.value: (
        "Solid presentation with minor issues. A few adjustments would improve "
        "audience engagement."
    ),
    PresentationRating.DEVELOPING.value: (
        "Noticeable nonverbal habits that may distract the audience. Targeted practice "
        "is recommended."
    ),
    PresentationRating.NEEDS_WORK.value: (
        "Significant posture, gaze, or movement issues that likely reduce credibility "
        "and audience connection."
    ),
}

DIMENSION_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "posture": {
        PresentationRating.EXCELLENT.value: "Upright, balanced stance without excessive forward or backward lean.",
        PresentationRating.GOOD.value: "Generally upright with occasional lean or shoulder asymmetry.",
        PresentationRating.DEVELOPING.value: "Frequent slouching, leaning, or closed posture.",
        PresentationRating.NEEDS_WORK.value: "Posture consistently undermines a confident, open presence.",
    },
    "gaze": {
        PresentationRating.EXCELLENT.value: "Head stays level and forward — good proxy for audience eye contact.",
        PresentationRating.GOOD.value: "Mostly forward-facing with brief glances downward.",
        PresentationRating.DEVELOPING.value: "Often looking down — may appear to read notes or avoid the audience.",
        PresentationRating.NEEDS_WORK.value: "Sustained downward gaze; audience connection is likely weak.",
    },
    "gestures": {
        PresentationRating.EXCELLENT.value: "Purposeful hand movement — neither frozen nor excessive.",
        PresentationRating.GOOD.value: "Adequate gesture variety with minor imbalance or stillness.",
        PresentationRating.DEVELOPING.value: "Hands too still, too active, or dominated by one side.",
        PresentationRating.NEEDS_WORK.value: "Gestures distract from the message or show little intentional signal.",
    },
    "composure": {
        PresentationRating.EXCELLENT.value: "Calm, controlled movement with low fidgeting and nervous gestures.",
        PresentationRating.GOOD.value: "Mostly composed with occasional fidgeting or hand-to-face contact.",
        PresentationRating.DEVELOPING.value: "Repetitive fidgeting or nervous movements are noticeable.",
        PresentationRating.NEEDS_WORK.value: "High fidgeting, hand-to-face contact, or rocking undermines delivery.",
    },
    "stability": {
        PresentationRating.EXCELLENT.value: "Steady head and torso — no rocking or erratic jerks.",
        PresentationRating.GOOD.value: "Generally stable with minor head movement.",
        PresentationRating.DEVELOPING.value: "Frequent head shifts or rocking motion detected.",
        PresentationRating.NEEDS_WORK.value: "Unstable movement patterns distract the audience.",
    },
}

# Maps categorical rating to 0–100 for CRUD-Module numeric fields.
RATING_TO_NUMERIC: dict[PresentationRating, float] = {
    PresentationRating.EXCELLENT: 92.0,
    PresentationRating.GOOD: 78.0,
    PresentationRating.DEVELOPING: 58.0,
    PresentationRating.NEEDS_WORK: 38.0,
}

FIDGETING_LEVEL_MAP: dict[PresentationRating, str] = {
    PresentationRating.EXCELLENT: "low",
    PresentationRating.GOOD: "low",
    PresentationRating.DEVELOPING: "medium",
    PresentationRating.NEEDS_WORK: "high",
}


@dataclass
class PresentationAssessment:
    overall: PresentationRating
    overall_meaning: str
    posture: PresentationRating
    posture_meaning: str
    gaze: PresentationRating
    gaze_meaning: str
    gestures: PresentationRating
    gestures_meaning: str
    composure: PresentationRating
    composure_meaning: str
    stability: PresentationRating
    stability_meaning: str
    dimension_summary: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, str | dict[str, str]]:
        return {
            "overall_presentation": self.overall.value,
            "overall_meaning": self.overall_meaning,
            "posture": self.posture.value,
            "posture_meaning": self.posture_meaning,
            "gaze": self.gaze.value,
            "gaze_meaning": self.gaze_meaning,
            "gestures": self.gestures.value,
            "gestures_meaning": self.gestures_meaning,
            "composure": self.composure.value,
            "composure_meaning": self.composure_meaning,
            "stability": self.stability.value,
            "stability_meaning": self.stability_meaning,
            "dimension_summary": self.dimension_summary,
        }


def _worst(*ratings: PresentationRating) -> PresentationRating:
    return max(ratings, key=lambda r: RATING_SEVERITY[r])


def _rate_ratio(ratio: float, good: float, developing: float, poor: float) -> PresentationRating:
    if ratio <= good:
        return PresentationRating.EXCELLENT
    if ratio <= developing:
        return PresentationRating.GOOD
    if ratio <= poor:
        return PresentationRating.DEVELOPING
    return PresentationRating.NEEDS_WORK


def _meaning(dimension: str, rating: PresentationRating) -> str:
    return DIMENSION_DESCRIPTIONS[dimension][rating.value]


def _rate_value(value: float, good: float, developing: float, poor: float) -> PresentationRating:
    """Lower values are better (e.g. lean angles, shoulder asymmetry cm)."""
    if value <= good:
        return PresentationRating.EXCELLENT
    if value <= developing:
        return PresentationRating.GOOD
    if value <= poor:
        return PresentationRating.DEVELOPING
    return PresentationRating.NEEDS_WORK


def _rate_hand_velocity(avg_mps: float) -> PresentationRating:
    """Purposeful presenter gesture band — not frozen, not frantic."""
    if avg_mps < 0.06:
        return PresentationRating.DEVELOPING
    if avg_mps <= 0.90:
        return PresentationRating.EXCELLENT
    if avg_mps <= 1.15:
        return PresentationRating.GOOD
    return PresentationRating.DEVELOPING


def assess_presentation(
    metrics: MotionMetrics,
    rule_counts: dict[str, int],
    total_frames: int,
    session_seconds: float,
) -> PresentationAssessment:
    n = max(total_frames, 1)
    ratio = lambda key: rule_counts.get(key, 0) / n

    posture = _worst(
        _rate_value(metrics.forward_lean_avg, 10.0, 18.0, 26.0),
        _rate_value(metrics.backward_lean_avg, 5.0, 10.0, 16.0),
        _rate_value(metrics.shoulder_alignment_diff_cm, 5.6, 8.8, 12.0),
        _rate_ratio(ratio("crossed_arms"), 0.05, 0.12, 0.25),
    )

    gaze = _rate_ratio(metrics.looking_down_ratio, 0.08, 0.20, 0.35)

    avg_hand_v = (metrics.left_hand_avg_velocity + metrics.right_hand_avg_velocity) / 2
    hands_static = ratio("hands_too_static") + ratio("body_too_static")

    gestures = _worst(
        _rate_hand_velocity(avg_hand_v),
        _rate_ratio(hands_static, 0.08, 0.20, 0.35),
        _rate_ratio(ratio("excessive_movement"), 0.18, 0.35, 0.50),
    )
    if metrics.hand_dominance_ratio >= 0.78:
        gestures = _worst(gestures, PresentationRating.DEVELOPING)

    hand_face = ratio("hand_near_face")
    fidget = ratio("fidgeting_left") + ratio("fidgeting_right")
    rocking = metrics.rocking_score

    composure = _worst(
        _rate_ratio(hand_face, 0.03, 0.10, 0.22),
        _rate_ratio(fidget, 0.06, 0.15, 0.28),
        _rate_ratio(rocking, 0.40, 0.80, 1.20),
    )
    if metrics.hand_near_face_ratio > 0.15:
        composure = _worst(composure, PresentationRating.DEVELOPING)
    if metrics.hand_near_face_ratio > 0.28:
        composure = PresentationRating.NEEDS_WORK

    sudden_rate = len(metrics.sudden_index) / max(session_seconds, 1)
    stability = _worst(
        _rate_ratio(1.0 - metrics.head_stability_score, 0.25, 0.45, 0.65),
        _rate_ratio(sudden_rate, 0.4, 0.8, 1.5),
        _rate_ratio(rocking, 0.40, 0.80, 1.20),
    )

    overall = _worst(posture, gaze, gestures, composure, stability)

    return PresentationAssessment(
        overall=overall,
        overall_meaning=RATING_DESCRIPTIONS[overall.value],
        posture=posture,
        posture_meaning=_meaning("posture", posture),
        gaze=gaze,
        gaze_meaning=_meaning("gaze", gaze),
        gestures=gestures,
        gestures_meaning=_meaning("gestures", gestures),
        composure=composure,
        composure_meaning=_meaning("composure", composure),
        stability=stability,
        stability_meaning=_meaning("stability", stability),
        dimension_summary={
            "posture": posture.value,
            "gaze": gaze.value,
            "gestures": gestures.value,
            "composure": composure.value,
            "stability": stability.value,
        },
    )


def numeric_from_rating(rating: PresentationRating) -> float:
    return RATING_TO_NUMERIC[rating]
