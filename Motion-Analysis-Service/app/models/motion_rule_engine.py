from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.models.motion_frame_data import MotionFrameData
from app.utils.geometry import (
    distance_2d,
    gesture_space_ratio,
    hand_near_face_detail,
    hand_to_face_distance_ratio,
    head_pitch_degrees,
    is_hand_near_face,
    norm_to_meters,
    posture_backward_lean_degrees,
    posture_forward_lean_degrees,
    shoulder_height_diff_cm,
    shoulder_height_diff_ratio,
    velocity_mps,
)


class RuleSeverity(str, Enum):
    EXCELLENT = "excellent"
    ACCEPTABLE = "acceptable"
    WARNING = "warning"
    POOR = "poor"
    INFO = "info"


@dataclass(frozen=True)
class RuleEvaluation:
    rule_id: str
    label: str
    severity: RuleSeverity
    message: str
    value: float | None = None


class MotionRuleEngine:
    """
    Rule thresholds inspired by MIT CommLab public-speaking guidance:
    - Nonverbal: upright posture, eye contact, purposeful gestures, minimize fidgeting
      https://mitcommlab.mit.edu/be/commkit/public-speaking-nonverbal/
    - Presentation skills: face audience, stand still, minimize distracting movement
      https://mitcommlab.mit.edu/cheme/commkit/slideshow-presentation-skills/
    Calibrate with pilot users on your capture setup.
    """

    # Forward lean — head/torso toward audience
    LEAN_FORWARD_EXCELLENT_DEG = 8.0
    LEAN_FORWARD_ACCEPTABLE_DEG = 18.0

    # Backward lean — reclining / slouching away (neck opens while torso stays upright)
    LEAN_BACKWARD_WARNING_DEG = 10.0
    LEAN_BACKWARD_POOR_DEG = 18.0

    # Shoulder symmetry — ratio of height diff to shoulder width (camera-angle tolerant)
    SHOULDER_EXCELLENT_RATIO = 0.14
    SHOULDER_WARNING_RATIO = 0.22
    SHOULDER_POOR_RATIO = 0.30

    # Legacy cm thresholds (derived from ratio × 40 cm shoulder width)
    SHOULDER_EXCELLENT_CM = SHOULDER_EXCELLENT_RATIO * 40.0
    SHOULDER_WARNING_CM = SHOULDER_WARNING_RATIO * 40.0

    # Hands too static — MIT: move with purpose; add deliberate gestures
    HAND_STATIC_VELOCITY_MPS = 0.04
    HAND_STATIC_MIN_SECONDS = 10.0

    # Whole upper body frozen — low engagement
    BODY_STATIC_VELOCITY_MPS = 0.035
    BODY_STATIC_MIN_SECONDS = 12.0

    # Excessive gesture noise — brief spikes during deliberate gestures are OK
    HAND_EXCESSIVE_VELOCITY_MPS = 1.05

    # Gaze — proxy for eye contact; avoid looking at floor/notes
    LOOKING_DOWN_PITCH_DEG = 22.0
    LOOKING_DOWN_MIN_RATIO = 0.25

    # Closed posture
    CROSSED_ARMS_RATIO = 0.52

    # Gesture balance
    HAND_DOMINANCE_RATIO = 0.78

    # Hand near face — palm/fingertip proximity (requires Hand Landmarker)
    HAND_FACE_WARNING_RATIO = 0.45
    HAND_FACE_POOR_RATIO = 0.32

    # Fidgeting — repetitive low-amplitude noise
    FIDGET_VELOCITY_MPS = 0.38
    FIDGET_AMPLITUDE_CM = 4.5
    FIDGET_FREQUENCY_HZ = 3.5

    # Sudden distracting jerks
    SUDDEN_WRIST_DELTA_RATIO = 0.32
    SUDDEN_HEAD_DELTA_RATIO = 0.42

    # Rocking torso (session metric threshold applied in service)
    ROCKING_SPINE_STD_DEG = 4.5

    SHOULDER_WIDTH_M = 0.40

    # Legacy aliases
    LEAN_EXCELLENT_DEG = LEAN_FORWARD_EXCELLENT_DEG
    LEAN_ACCEPTABLE_DEG = LEAN_FORWARD_ACCEPTABLE_DEG

    def evaluate_leaning_forward(self, frame: MotionFrameData) -> RuleEvaluation:
        lean = posture_forward_lean_degrees(frame)
        if lean < self.LEAN_FORWARD_EXCELLENT_DEG:
            severity = RuleSeverity.EXCELLENT
            message = f"Forward lean {lean:.1f}° — upright, audience-facing"
        elif lean <= self.LEAN_FORWARD_ACCEPTABLE_DEG:
            severity = RuleSeverity.ACCEPTABLE
            message = f"Forward lean {lean:.1f}° — acceptable"
        else:
            severity = RuleSeverity.WARNING
            message = f"Forward lean {lean:.1f}° — stand taller, face the audience"
        return RuleEvaluation(
            rule_id="leaning_forward",
            label="Leaning Forward",
            severity=severity,
            message=message,
            value=lean,
        )

    def evaluate_leaning_backward(self, frame: MotionFrameData) -> RuleEvaluation:
        lean = posture_backward_lean_degrees(frame)
        if lean < self.LEAN_BACKWARD_WARNING_DEG:
            severity = RuleSeverity.EXCELLENT
            message = f"Backward lean {lean:.1f}° — upright posture"
        elif lean <= self.LEAN_BACKWARD_POOR_DEG:
            severity = RuleSeverity.WARNING
            message = f"Backward lean {lean:.1f}° — sit/stand upright toward audience"
        else:
            severity = RuleSeverity.POOR
            message = f"Backward lean {lean:.1f}° — avoid reclining away from audience"
        return RuleEvaluation(
            rule_id="leaning_backward",
            label="Leaning Backward",
            severity=severity,
            message=message,
            value=lean,
        )

    def evaluate_hand_near_face(self, frame: MotionFrameData) -> RuleEvaluation | None:
        candidates: list[tuple[str, str, float]] = []
        for side in ("left", "right"):
            near, part, ratio = hand_near_face_detail(
                frame, side, self.HAND_FACE_WARNING_RATIO
            )
            if near:
                candidates.append((side, part, ratio))

        if not candidates:
            return None

        side, part, closest = min(candidates, key=lambda item: item[2])
        tracked = frame.hand_is_tracked(side)
        severity = (
            RuleSeverity.POOR
            if closest < self.HAND_FACE_POOR_RATIO
            else RuleSeverity.WARNING
        )
        source = "hand" if tracked else "wrist (estimate)"
        return RuleEvaluation(
            rule_id="hand_near_face",
            label="Hand Near Face",
            severity=severity,
            message=(
                f"{side.title()} {part} near face ({source}) — "
                "keep gestures open and visible"
            ),
            value=closest,
        )

    def evaluate_body_stillness(
        self,
        left_velocity: float,
        right_velocity: float,
        head_velocity: float,
        static_duration_sec: float,
    ) -> RuleEvaluation | None:
        avg = (left_velocity + right_velocity + head_velocity) / 3
        if (
            avg < self.BODY_STATIC_VELOCITY_MPS
            and static_duration_sec >= self.BODY_STATIC_MIN_SECONDS
        ):
            return RuleEvaluation(
                rule_id="body_too_static",
                label="Body Too Static",
                severity=RuleSeverity.WARNING,
                message=(
                    f"Upper body still for {static_duration_sec:.0f}s — "
                    "add purposeful gestures (MIT: move with purpose)"
                ),
                value=avg,
            )
        return None

    def evaluate_shoulder_alignment(self, frame: MotionFrameData) -> RuleEvaluation:
        diff_ratio = shoulder_height_diff_ratio(
            frame.left_shoulder,
            frame.right_shoulder,
            frame.shoulder_width_norm,
        )
        diff_cm = diff_ratio * self.SHOULDER_WIDTH_M * 100
        if diff_ratio < self.SHOULDER_EXCELLENT_RATIO:
            severity = RuleSeverity.EXCELLENT
            message = f"Shoulder alignment {diff_cm:.1f} cm — level, upright"
        elif diff_ratio < self.SHOULDER_WARNING_RATIO:
            severity = RuleSeverity.ACCEPTABLE
            message = f"Shoulder alignment {diff_cm:.1f} cm — minor asymmetry"
        elif diff_ratio < self.SHOULDER_POOR_RATIO:
            severity = RuleSeverity.WARNING
            message = f"Shoulder alignment {diff_cm:.1f} cm — noticeable tilt"
        else:
            severity = RuleSeverity.POOR
            message = f"Shoulder alignment {diff_cm:.1f} cm — poor symmetry"
        return RuleEvaluation(
            rule_id="shoulder_alignment",
            label="Shoulder Alignment",
            severity=severity,
            message=message,
            value=diff_cm,
        )

    def evaluate_hand_stillness(
        self,
        left_velocity: float,
        right_velocity: float,
        static_duration_sec: float,
    ) -> RuleEvaluation | None:
        avg_velocity = (left_velocity + right_velocity) / 2
        if (
            avg_velocity < self.HAND_STATIC_VELOCITY_MPS
            and static_duration_sec >= self.HAND_STATIC_MIN_SECONDS
        ):
            return RuleEvaluation(
                rule_id="hands_too_static",
                label="Hands Too Static",
                severity=RuleSeverity.WARNING,
                message=(
                    f"Hands still {static_duration_sec:.0f}s — use deliberate gestures "
                    "to emphasize key points"
                ),
                value=avg_velocity,
            )
        return None

    def evaluate_excessive_movement(
        self, left_velocity: float, right_velocity: float
    ) -> RuleEvaluation | None:
        avg_velocity = (left_velocity + right_velocity) / 2
        if avg_velocity > self.HAND_EXCESSIVE_VELOCITY_MPS:
            return RuleEvaluation(
                rule_id="excessive_movement",
                label="Excessive Movement",
                severity=RuleSeverity.WARNING,
                message=f"Hand velocity {avg_velocity:.2f} m/s — distracting gesture speed",
                value=avg_velocity,
            )
        return None

    def evaluate_looking_down(self, pitch_deg: float) -> RuleEvaluation | None:
        if pitch_deg > self.LOOKING_DOWN_PITCH_DEG:
            return RuleEvaluation(
                rule_id="looking_down",
                label="Looking Down",
                severity=RuleSeverity.WARNING,
                message=f"Gaze down {pitch_deg:.1f}° — engage audience with eye contact",
                value=pitch_deg,
            )
        return None

    def evaluate_looking_down_session(self, looking_down_ratio: float) -> RuleEvaluation | None:
        if looking_down_ratio > self.LOOKING_DOWN_MIN_RATIO:
            return RuleEvaluation(
                rule_id="looking_down_session",
                label="Looking Down (Session)",
                severity=RuleSeverity.WARNING,
                message=(
                    f"Looking down {looking_down_ratio * 100:.0f}% of session — "
                    "keep gaze toward audience"
                ),
                value=looking_down_ratio,
            )
        return None

    def evaluate_crossed_arms(self, frame: MotionFrameData) -> RuleEvaluation | None:
        sw = frame.shoulder_width_norm
        if sw < 1e-6:
            return None

        left_wrist_to_right_elbow = distance_2d(frame.left_wrist, frame.right_elbow) / sw
        right_wrist_to_left_elbow = distance_2d(frame.right_wrist, frame.left_elbow) / sw

        if (
            left_wrist_to_right_elbow < self.CROSSED_ARMS_RATIO
            and right_wrist_to_left_elbow < self.CROSSED_ARMS_RATIO
        ):
            return RuleEvaluation(
                rule_id="crossed_arms",
                label="Crossed Arms",
                severity=RuleSeverity.WARNING,
                message="Crossed arms detected — open posture recommended",
                value=min(left_wrist_to_right_elbow, right_wrist_to_left_elbow),
            )
        return None

    def evaluate_one_hand_dominance(
        self, left_total_m: float, right_total_m: float
    ) -> RuleEvaluation | None:
        total = left_total_m + right_total_m
        if total < 1e-6:
            return None

        left_ratio = left_total_m / total
        right_ratio = right_total_m / total
        dominant = max(left_ratio, right_ratio)

        if dominant >= self.HAND_DOMINANCE_RATIO:
            side = "left" if left_ratio > right_ratio else "right"
            return RuleEvaluation(
                rule_id="one_hand_dominance",
                label="One-Hand Dominance",
                severity=RuleSeverity.INFO,
                message=f"{side.title()} hand dominant ({dominant * 100:.0f}%) — balance gestures",
                value=dominant,
            )
        return None

    def evaluate_fidgeting(
        self,
        velocity_mps: float,
        amplitude_cm: float,
        frequency_hz: float,
    ) -> RuleEvaluation | None:
        if (
            velocity_mps >= self.FIDGET_VELOCITY_MPS
            and amplitude_cm < self.FIDGET_AMPLITUDE_CM
            and frequency_hz >= self.FIDGET_FREQUENCY_HZ
        ):
            return RuleEvaluation(
                rule_id="fidgeting",
                label="Fidgeting",
                severity=RuleSeverity.WARNING,
                message=(
                    f"Fidgeting detected (v={velocity_mps:.2f} m/s, "
                    f"amp={amplitude_cm:.1f} cm, f={frequency_hz:.1f} Hz)"
                ),
                value=velocity_mps,
            )
        return None

    def evaluate_head_stability(self, score: float) -> str:
        if score >= 0.7:
            return "stable"
        if score >= 0.4:
            return "moderate"
        return "unstable"

    def evaluate_fidgeting_level(self, score: float) -> str:
        if score < 0.3:
            return "low"
        if score < 0.6:
            return "medium"
        return "high"

    def evaluate_sudden_move(self, sudden_count: int, session_seconds: float) -> RuleEvaluation | None:
        if session_seconds <= 0:
            return None
        rate = sudden_count / session_seconds
        if rate > 1.2:
            return RuleEvaluation(
                rule_id="sudden_movements",
                label="Sudden Movements",
                severity=RuleSeverity.WARNING,
                message=f"Frequent sudden movements ({sudden_count} events)",
                value=rate,
            )
        return None

    def gesture_space_ratio(self, frame: MotionFrameData, hand_side: str) -> float:
        hand_point = frame.hand_tracking_point(hand_side)
        shoulder = frame.left_shoulder if hand_side == "left" else frame.right_shoulder
        return gesture_space_ratio(hand_point, shoulder, frame.shoulder_width_norm)

    def is_sudden_movement(
        self,
        current: MotionFrameData,
        previous: MotionFrameData,
        body_part: str,
    ) -> bool:
        sw = current.shoulder_width_norm
        if sw < 1e-6:
            return False

        if body_part in ("left_hand", "right_hand"):
            side = body_part.replace("_hand", "")
            if not current.hand_is_tracked(side) or not previous.hand_is_tracked(side):
                body_part = f"{side}_wrist"

        attr = {
            "head": (current.nose, previous.nose),
            "left_wrist": (current.left_wrist, previous.left_wrist),
            "right_wrist": (current.right_wrist, previous.right_wrist),
            "left_hand": (current.hand_tracking_point("left"), previous.hand_tracking_point("left")),
            "right_hand": (current.hand_tracking_point("right"), previous.hand_tracking_point("right")),
        }.get(body_part)
        if not attr:
            return False

        threshold = (
            self.SUDDEN_HEAD_DELTA_RATIO
            if body_part == "head"
            else self.SUDDEN_WRIST_DELTA_RATIO
        )
        delta = distance_2d(attr[0], attr[1]) / sw
        return delta > threshold

    def hand_velocity_mps(
        self,
        current: MotionFrameData,
        previous: MotionFrameData | None,
        side: str,
        dt_seconds: float,
    ) -> float:
        """Hand movement speed using palm center when tracked, else pose wrist."""
        if previous is None or dt_seconds <= 0:
            return 0.0

        point_curr = current.hand_tracking_point(side)
        point_prev = previous.hand_tracking_point(side)
        return velocity_mps(
            point_curr,
            point_prev,
            dt_seconds,
            current.shoulder_width_norm,
            self.SHOULDER_WIDTH_M,
        )

    def wrist_velocity_mps(
        self,
        current: MotionFrameData,
        previous: MotionFrameData | None,
        side: str,
        dt_seconds: float,
    ) -> float:
        return self.hand_velocity_mps(current, previous, side, dt_seconds)

    def hand_movement_m(
        self,
        current: MotionFrameData,
        previous: MotionFrameData | None,
        side: str,
    ) -> float:
        if previous is None:
            return 0.0
        point_curr = current.hand_tracking_point(side)
        point_prev = previous.hand_tracking_point(side)
        dist_norm = distance_2d(point_curr, point_prev)
        return norm_to_meters(
            dist_norm, current.shoulder_width_norm, self.SHOULDER_WIDTH_M
        )

    def wrist_movement_m(
        self,
        current: MotionFrameData,
        previous: MotionFrameData | None,
        side: str,
    ) -> float:
        return self.hand_movement_m(current, previous, side)
