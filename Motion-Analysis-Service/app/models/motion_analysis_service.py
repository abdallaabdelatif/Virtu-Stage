from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
import math
import uuid

import numpy as np

from app.models.motion_analysis_result import MotionAnalysisResult, PostureType
from app.models.motion_frame_data import MotionFrameData
from app.models.motion_metrics import MotionMetrics
from app.models.motion_rule_engine import MotionRuleEngine, RuleEvaluation, RuleSeverity
from app.models.presentation_ratings import (
    FIDGETING_LEVEL_MAP,
    assess_presentation,
    numeric_from_rating,
)
from app.utils.geometry import (
    clamp,
    head_pitch_degrees,
    head_tilt_from_vertical_degrees,
    is_hand_near_face,
    norm_to_meters,
    posture_backward_lean_degrees,
    posture_forward_lean_degrees,
    shoulder_height_diff_cm,
    spine_tilt_degrees,
    velocity_mps,
)


@dataclass
class FrameEvaluation:
    frame_index: int
    timestamp_ms: int
    triggered_rules: list[RuleEvaluation] = field(default_factory=list)
    posture_type: PostureType = PostureType.NEUTRAL
    left_hand_velocity_mps: float = 0.0
    right_hand_velocity_mps: float = 0.0
    forward_lean_deg: float = 0.0
    head_pitch_deg: float = 0.0


class MotionAnalysisService:
    def __init__(self, rule_engine: MotionRuleEngine | None = None) -> None:
        self.rule_engine = rule_engine or MotionRuleEngine()
        self._static_duration_sec = 0.0
        self._body_static_duration_sec = 0.0
        self._max_body_static_duration_sec = 0.0
        self._left_wrist_history: deque[tuple[int, float, float]] = deque(maxlen=120)
        self._right_wrist_history: deque[tuple[int, float, float]] = deque(maxlen=120)

    def evaluate_frame(
        self,
        frame: MotionFrameData,
        previous: MotionFrameData | None,
        fps: float,
    ) -> FrameEvaluation:
        dt = 1.0 / fps if fps > 0 else 1.0 / 30.0

        left_v = self.rule_engine.wrist_velocity_mps(frame, previous, "left", dt)
        right_v = self.rule_engine.wrist_velocity_mps(frame, previous, "right", dt)

        head_v = 0.0
        if previous is not None:
            head_v = velocity_mps(
                frame.nose,
                previous.nose,
                dt,
                frame.shoulder_width_norm,
                self.rule_engine.SHOULDER_WIDTH_M,
            )

        avg_v = (left_v + right_v) / 2
        if avg_v < self.rule_engine.HAND_STATIC_VELOCITY_MPS:
            self._static_duration_sec += dt
        else:
            self._static_duration_sec = 0.0

        body_avg_v = (left_v + right_v + head_v) / 3
        if body_avg_v < self.rule_engine.BODY_STATIC_VELOCITY_MPS:
            self._body_static_duration_sec += dt
            self._max_body_static_duration_sec = max(
                self._max_body_static_duration_sec, self._body_static_duration_sec
            )
        else:
            self._body_static_duration_sec = 0.0

        if previous is not None:
            left_point = frame.hand_tracking_point("left")
            right_point = frame.hand_tracking_point("right")
            self._left_wrist_history.append(
                (frame.timestamp_ms, left_point.x, left_point.y)
            )
            self._right_wrist_history.append(
                (frame.timestamp_ms, right_point.x, right_point.y)
            )

        triggered: list[RuleEvaluation] = []

        lean_eval = self.rule_engine.evaluate_leaning_forward(frame)
        triggered.append(lean_eval)

        back_eval = self.rule_engine.evaluate_leaning_backward(frame)
        triggered.append(back_eval)

        shoulder_eval = self.rule_engine.evaluate_shoulder_alignment(frame)
        triggered.append(shoulder_eval)

        static_eval = self.rule_engine.evaluate_hand_stillness(
            left_v, right_v, self._static_duration_sec
        )
        if static_eval:
            triggered.append(static_eval)

        body_static_eval = self.rule_engine.evaluate_body_stillness(
            left_v, right_v, head_v, self._body_static_duration_sec
        )
        if body_static_eval:
            triggered.append(body_static_eval)

        hand_face_eval = self.rule_engine.evaluate_hand_near_face(frame)
        if hand_face_eval:
            triggered.append(hand_face_eval)

        excess_eval = self.rule_engine.evaluate_excessive_movement(left_v, right_v)
        if excess_eval:
            triggered.append(excess_eval)

        pitch = head_pitch_degrees(frame.nose, frame.mid_shoulder)
        look_eval = self.rule_engine.evaluate_looking_down(pitch)
        if look_eval:
            triggered.append(look_eval)

        crossed_eval = self.rule_engine.evaluate_crossed_arms(frame)
        if crossed_eval:
            triggered.append(crossed_eval)

        for side, velocity, history in (
            ("left", left_v, self._left_wrist_history),
            ("right", right_v, self._right_wrist_history),
        ):
            if len(history) < 12:
                continue
            amp_cm, freq_hz = self._oscillation_stats(history, frame.shoulder_width_norm)
            fidget_eval = self.rule_engine.evaluate_fidgeting(velocity, amp_cm, freq_hz)
            if fidget_eval:
                fidget_eval = RuleEvaluation(
                    rule_id=f"fidgeting_{side}",
                    label=f"Fidgeting ({side})",
                    severity=fidget_eval.severity,
                    message=fidget_eval.message,
                    value=fidget_eval.value,
                )
                triggered.append(fidget_eval)

        if previous is not None:
            for part in ("left_hand", "right_hand"):
                side = part.replace("_hand", "")
                if not frame.hand_is_tracked(side):
                    part = f"{side}_wrist"
                if self.rule_engine.is_sudden_movement(frame, previous, part):
                    triggered.append(
                        RuleEvaluation(
                            rule_id=f"sudden_{part}",
                            label=f"Sudden {part.replace('_', ' ').title()}",
                            severity=RuleSeverity.WARNING,
                            message=f"Sudden {part.replace('_', ' ')} movement detected",
                        )
                    )

        posture_type = self._resolve_posture_type(
            triggered, lean_eval, back_eval, shoulder_eval
        )

        return FrameEvaluation(
            frame_index=frame.frame_index,
            timestamp_ms=frame.timestamp_ms,
            triggered_rules=triggered,
            posture_type=posture_type,
            left_hand_velocity_mps=left_v,
            right_hand_velocity_mps=right_v,
            forward_lean_deg=lean_eval.value or 0.0,
            head_pitch_deg=pitch,
        )

    def analyze_session(
        self,
        frames: list[MotionFrameData],
        fps: float,
        session_id: str | None = None,
    ) -> MotionAnalysisResult:
        if not frames:
            raise ValueError("No frames to analyze")

        self.reset_session_state()
        session_id = session_id or str(uuid.uuid4())
        metrics = MotionMetrics()
        recommendations: list[str] = []
        frame_evaluations: list[FrameEvaluation] = []

        nose_x: list[float] = []
        nose_y: list[float] = []
        head_velocities: list[float] = []
        lean_angles: list[float] = []
        pitch_angles: list[float] = []
        looking_down_frames = 0
        left_velocities: list[float] = []
        right_velocities: list[float] = []
        left_total_m = 0.0
        right_total_m = 0.0
        shoulder_diffs: list[float] = []
        spine_tilts: list[float] = []
        backward_lean_angles: list[float] = []
        hand_near_face_frames = 0
        hand_tracked_frames = 0
        sudden_events: list[dict] = []
        posture_counts: dict[str, int] = defaultdict(int)
        rule_counts: dict[str, int] = defaultdict(int)

        previous: MotionFrameData | None = None
        dt = 1.0 / fps if fps > 0 else 1.0 / 30.0

        for frame in frames:
            evaluation = self.evaluate_frame(frame, previous, fps)
            frame_evaluations.append(evaluation)
            posture_counts[evaluation.posture_type.value] += 1

            for rule in evaluation.triggered_rules:
                if rule.severity in (
                    RuleSeverity.WARNING,
                    RuleSeverity.POOR,
                    RuleSeverity.INFO,
                ):
                    rule_counts[rule.rule_id] += 1

            nose_x.append(frame.nose.x)
            nose_y.append(frame.nose.y)
            lean_angles.append(posture_forward_lean_degrees(frame))
            backward_lean_angles.append(posture_backward_lean_degrees(frame))
            if is_hand_near_face(frame, self.rule_engine.HAND_FACE_WARNING_RATIO):
                hand_near_face_frames += 1
            if frame.hand_is_tracked("left") or frame.hand_is_tracked("right"):
                hand_tracked_frames += 1
            pitch = head_pitch_degrees(frame.nose, frame.mid_shoulder)
            pitch_angles.append(pitch)
            if pitch > self.rule_engine.LOOKING_DOWN_PITCH_DEG:
                looking_down_frames += 1

            shoulder_diffs.append(
                shoulder_height_diff_cm(
                    frame.left_shoulder,
                    frame.right_shoulder,
                    frame.shoulder_width_norm,
                    self.rule_engine.SHOULDER_WIDTH_M,
                )
            )
            spine_tilts.append(
                spine_tilt_degrees(frame.mid_shoulder, frame.mid_hip)
            )

            if previous is not None:
                head_vel = velocity_mps(
                    frame.nose,
                    previous.nose,
                    dt,
                    frame.shoulder_width_norm,
                    self.rule_engine.SHOULDER_WIDTH_M,
                )
                head_velocities.append(head_vel)

                left_vel = self.rule_engine.wrist_velocity_mps(
                    frame, previous, "left", dt
                )
                right_vel = self.rule_engine.wrist_velocity_mps(
                    frame, previous, "right", dt
                )
                left_velocities.append(left_vel)
                right_velocities.append(right_vel)
                left_total_m += self.rule_engine.wrist_movement_m(frame, previous, "left")
                right_total_m += self.rule_engine.wrist_movement_m(
                    frame, previous, "right"
                )

                for side in ("left", "right"):
                    part = f"{side}_hand" if frame.hand_is_tracked(side) else f"{side}_wrist"
                    if self.rule_engine.is_sudden_movement(frame, previous, part):
                        sudden_events.append(
                            {
                                "body_part": part,
                                "timestamp_ms": frame.timestamp_ms,
                                "frame_index": frame.frame_index,
                            }
                        )

            previous = frame

        session_seconds = len(frames) * dt
        metrics.sudden_index = sudden_events
        metrics.repetitive_index = self.calculate_repetitive_index(sudden_events)

        metrics.head_movement_variance = float(
            np.var(nose_x) + np.var(nose_y) if nose_x else 0.0
        )
        metrics.head_avg_velocity = float(np.mean(head_velocities)) if head_velocities else 0.0
        metrics.max_rotation_head_degree = max(
            [head_tilt_from_vertical_degrees(f.nose, f.mid_shoulder) for f in frames],
            default=0.0,
        )
        metrics.head_pitch_avg = float(np.mean(pitch_angles)) if pitch_angles else 0.0
        metrics.forward_lean_avg = float(np.mean(lean_angles)) if lean_angles else 0.0
        metrics.backward_lean_avg = (
            float(np.mean(backward_lean_angles)) if backward_lean_angles else 0.0
        )
        metrics.hand_near_face_ratio = hand_near_face_frames / len(frames)
        metrics.hand_tracking_ratio = hand_tracked_frames / len(frames)
        metrics.body_static_duration_sec = self._max_body_static_duration_sec
        spine_std = float(np.std(spine_tilts)) if spine_tilts else 0.0
        metrics.rocking_score = round(
            clamp(spine_std / self.rule_engine.ROCKING_SPINE_STD_DEG, 0, 2.0), 3
        )
        metrics.looking_down_ratio = looking_down_frames / len(frames)

        variance_penalty = clamp(metrics.head_movement_variance * 12, 0, 1)
        velocity_penalty = clamp(metrics.head_avg_velocity / 1.2, 0, 1)
        metrics.head_stability_score = round(
            clamp(1.0 - (variance_penalty * 0.6 + velocity_penalty * 0.4)), 4
        )

        metrics.shoulder_alignment_diff_cm = float(np.mean(shoulder_diffs)) if shoulder_diffs else 0.0

        metrics.left_hand_avg_velocity = float(np.mean(left_velocities)) if left_velocities else 0.0
        metrics.right_hand_avg_velocity = (
            float(np.mean(right_velocities)) if right_velocities else 0.0
        )
        metrics.left_hand_total_movement_m = left_total_m
        metrics.right_hand_total_movement_m = right_total_m

        total_hand = left_total_m + right_total_m
        if total_hand > 0:
            metrics.hand_dominance_ratio = max(left_total_m, right_total_m) / total_hand

        fidget_frames = rule_counts.get("fidgeting_left", 0) + rule_counts.get(
            "fidgeting_right", 0
        )
        metrics.fidgeting_score = round(
            clamp(
                fidget_frames / max(len(frames), 1) * 1.0
                + len(metrics.repetitive_index) * 0.08
                + len(sudden_events) / max(session_seconds, 1) * 0.04
            ),
            4,
        )

        metrics.rule_trigger_counts = dict(rule_counts)
        metrics.posture_type_counts = dict(posture_counts)

        assessment = assess_presentation(
            metrics, rule_counts, len(frames), session_seconds
        )
        metrics.presentation_overall = assessment.overall.value
        metrics.posture_rating = assessment.posture.value
        metrics.gaze_rating = assessment.gaze.value
        metrics.gesture_rating = assessment.gestures.value
        metrics.composure_rating = assessment.composure.value
        metrics.stability_rating = assessment.stability.value

        metrics.posture_score = numeric_from_rating(assessment.posture)
        metrics.posture_quality = metrics.posture_score
        metrics.hand_movement_score = numeric_from_rating(assessment.gestures)
        metrics.motion_overall_score = numeric_from_rating(assessment.overall)
        metrics.fidgeting_level = FIDGETING_LEVEL_MAP[assessment.composure]
        metrics.nervousness_indicator = round(
            100.0 - numeric_from_rating(assessment.composure), 2
        )

        recommendations.extend(
            self._build_recommendations(metrics, rule_counts, session_seconds, len(frames))
        )

        dominant_posture = (
            max(posture_counts, key=posture_counts.get) if posture_counts else PostureType.NEUTRAL.value
        )

        return MotionAnalysisResult(
            timestamp=datetime.now(timezone.utc),
            session_id=session_id,
            metrics=metrics,
            presentation=assessment,
            motion_overall_score=metrics.motion_overall_score,
            recommendations=recommendations,
            dominant_posture_type=dominant_posture,
        )

    def calculate_repetitive_index(
        self, sudden_events: list[dict], window_ms: int = 4000, min_count: int = 6
    ) -> list[dict]:
        if not sudden_events:
            return []

        grouped: dict[str, list[dict]] = defaultdict(list)
        for event in sudden_events:
            grouped[event["body_part"]].append(event)

        repetitive: list[dict] = []
        for body_part, events in grouped.items():
            events.sort(key=lambda e: e["timestamp_ms"])
            cluster: list[dict] = []
            for event in events:
                if not cluster:
                    cluster = [event]
                    continue
                if event["timestamp_ms"] - cluster[-1]["timestamp_ms"] <= window_ms:
                    cluster.append(event)
                else:
                    if len(cluster) >= min_count:
                        repetitive.append(
                            {
                                "body_part": body_part,
                                "count": len(cluster),
                                "timestamps_ms": [e["timestamp_ms"] for e in cluster],
                            }
                        )
                    cluster = [event]
            if len(cluster) >= min_count:
                repetitive.append(
                    {
                        "body_part": body_part,
                        "count": len(cluster),
                        "timestamps_ms": [e["timestamp_ms"] for e in cluster],
                    }
                )
        return repetitive

    def calculate_sudden_index(
        self, frames: list[MotionFrameData]
    ) -> list[dict]:
        sudden: list[dict] = []
        previous: MotionFrameData | None = None
        for frame in frames:
            if previous is not None:
                for side in ("left", "right"):
                    part = f"{side}_hand" if frame.hand_is_tracked(side) else f"{side}_wrist"
                    if self.rule_engine.is_sudden_movement(frame, previous, part):
                        sudden.append(
                            {
                                "body_part": part,
                                "timestamp_ms": frame.timestamp_ms,
                                "frame_index": frame.frame_index,
                            }
                        )
            previous = frame
        return sudden

    def calculate_fidgeting_score(
        self,
        sudden_index: list[dict],
        repetitive_index: list[dict],
        frame_count: int,
        session_seconds: float,
    ) -> float:
        fidget_base = len(repetitive_index) * 0.2 + len(sudden_index) / max(session_seconds, 1) * 0.1
        return clamp(fidget_base + (frame_count and 0 or 0))

    def calculate_head_stability_score(
        self, head_variance: float, head_avg_velocity: float
    ) -> float:
        variance_penalty = clamp(head_variance * 50, 0, 1)
        velocity_penalty = clamp(head_avg_velocity / 0.5, 0, 1)
        return clamp(1.0 - (variance_penalty * 0.6 + velocity_penalty * 0.4))

    def indicate_nervousness(self, metrics: MotionMetrics, sudden_count: int, session_seconds: float) -> float:
        return clamp(
            metrics.fidgeting_score * 0.4
            + metrics.looking_down_ratio * 0.2
            + (1.0 - metrics.head_stability_score) * 0.2
            + min(sudden_count / max(session_seconds, 1), 1.0) * 0.2
        )

    def _oscillation_stats(
        self,
        history: deque[tuple[int, float, float]],
        shoulder_width_norm: float,
    ) -> tuple[float, float]:
        if len(history) < 12 or shoulder_width_norm < 1e-6:
            return 0.0, 0.0

        xs = [p[1] for p in history]
        ys = [p[2] for p in history]
        times = [p[0] for p in history]

        amp_norm = max(
            math.hypot(max(xs) - min(xs), max(ys) - min(ys)),
            1e-6,
        )
        amp_cm = norm_to_meters(amp_norm, shoulder_width_norm, self.rule_engine.SHOULDER_WIDTH_M) * 100

        direction_changes = 0
        prev_dx = xs[1] - xs[0]
        prev_dy = ys[1] - ys[0]
        for i in range(2, len(xs)):
            dx = xs[i] - xs[i - 1]
            dy = ys[i] - ys[i - 1]
            if prev_dx * dx < 0 or prev_dy * dy < 0:
                direction_changes += 1
            prev_dx, prev_dy = dx, dy

        duration_sec = max((times[-1] - times[0]) / 1000.0, 1e-3)
        frequency_hz = direction_changes / duration_sec / 2
        return amp_cm, frequency_hz

    def _resolve_posture_type(
        self,
        triggered: list[RuleEvaluation],
        lean_eval: RuleEvaluation,
        back_eval: RuleEvaluation,
        shoulder_eval: RuleEvaluation,
    ) -> PostureType:
        priority = [
            (PostureType.HAND_NEAR_FACE, "hand_near_face"),
            (PostureType.CROSSED_ARMS, "crossed_arms"),
            (PostureType.FIDGETING, "fidgeting_left"),
            (PostureType.FIDGETING, "fidgeting_right"),
            (PostureType.EXCESSIVE_HAND_MOVEMENT, "excessive_movement"),
            (PostureType.BODY_TOO_STATIC, "body_too_static"),
            (PostureType.HANDS_TOO_STATIC, "hands_too_static"),
            (PostureType.LOOKING_DOWN, "looking_down"),
            (PostureType.ONE_HAND_DOMINANT, "one_hand_dominance"),
            (PostureType.LEANING_BACKWARD, "leaning_backward"),
            (PostureType.LEANING_FORWARD_WARNING, "leaning_forward"),
            (PostureType.SHOULDER_MISALIGNMENT, "shoulder_alignment"),
        ]
        for posture, rule_id in priority:
            match = next((r for r in triggered if r.rule_id == rule_id), None)
            if match is None:
                continue
            if rule_id in ("leaning_forward", "leaning_backward", "shoulder_alignment"):
                if match.severity in (RuleSeverity.WARNING, RuleSeverity.POOR):
                    return posture
            elif rule_id == "one_hand_dominance":
                if match.severity == RuleSeverity.INFO:
                    return posture
            else:
                return posture

        if (
            lean_eval.severity == RuleSeverity.EXCELLENT
            and back_eval.severity == RuleSeverity.EXCELLENT
            and shoulder_eval.severity == RuleSeverity.EXCELLENT
        ):
            return PostureType.EXCELLENT
        if lean_eval.severity == RuleSeverity.ACCEPTABLE:
            return PostureType.ACCEPTABLE
        return PostureType.NEUTRAL

    def _build_recommendations(
        self,
        metrics: MotionMetrics,
        rule_counts: dict[str, int],
        session_seconds: float,
        total_frames: int,
    ) -> list[str]:
        recs: list[str] = []
        frame_ratio = lambda key: rule_counts.get(key, 0) / max(total_frames, 1)

        if frame_ratio("leaning_forward") > 0.25:
            recs.append("Stand taller and face the audience — reduce forward lean.")
        if frame_ratio("leaning_backward") > 0.20:
            recs.append("Sit or stand upright toward the audience — avoid reclining backward.")
        if frame_ratio("shoulder_alignment") > 0.35:
            recs.append("Level your shoulders for a confident, symmetrical posture.")
        if frame_ratio("hands_too_static") > 0.15 or frame_ratio("body_too_static") > 0.12:
            recs.append(
                "Add purposeful gestures — upper body was still for extended periods."
            )
        if frame_ratio("excessive_movement") > 0.25:
            recs.append("Minimize distracting hand movement — keep gestures deliberate.")
        if frame_ratio("hand_near_face") > 0.10:
            recs.append("Keep hands away from your face — open, visible gestures engage the audience.")
        if metrics.looking_down_ratio > self.rule_engine.LOOKING_DOWN_MIN_RATIO:
            recs.append(
                f"Maintain eye-line with the audience — looking down "
                f"{metrics.looking_down_ratio * 100:.0f}% of the session."
            )
        if frame_ratio("crossed_arms") > 0.10:
            recs.append("Open your posture — avoid crossed arms.")
        dominance = self.rule_engine.evaluate_one_hand_dominance(
            metrics.left_hand_total_movement_m,
            metrics.right_hand_total_movement_m,
        )
        if dominance:
            recs.append(dominance.message)
        if metrics.fidgeting_level in ("medium", "high"):
            recs.append("Reduce repetitive fidgeting — practice steadier, purposeful movement.")
        if metrics.rocking_score > 1.0:
            recs.append("Minimize rocking — stand still with upright posture (MIT slideshow guidance).")
        sudden_eval = self.rule_engine.evaluate_sudden_move(
            len(metrics.sudden_index), session_seconds
        )
        if sudden_eval:
            recs.append(sudden_eval.message)
        if not recs:
            recs.append(
                "Strong nonverbal delivery — upright posture, steady gaze, and purposeful gestures."
            )
        return recs

    def reset_session_state(self) -> None:
        self._static_duration_sec = 0.0
        self._body_static_duration_sec = 0.0
        self._max_body_static_duration_sec = 0.0
        self._left_wrist_history.clear()
        self._right_wrist_history.clear()
