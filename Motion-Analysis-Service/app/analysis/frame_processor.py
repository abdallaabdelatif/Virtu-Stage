from __future__ import annotations

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from app.models.motion_frame_data import MotionFrameData
from app.pose.frame_quality import is_tracking_reliable
from app.pose.hand_tracking import attach_hands, extract_hands
from app.pose.landmark_smoother import LandmarkSmoother
from app.pose.model_paths import resolve_hand_model, resolve_pose_model
from app.visualization.overlay import build_motion_frame


class FrameProcessor:
    def __init__(self) -> None:
        pose_options = vision.PoseLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=resolve_pose_model()),
            running_mode=vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=0.6,
            min_pose_presence_confidence=0.6,
            min_tracking_confidence=0.6,
        )
        hand_options = vision.HandLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=resolve_hand_model()),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        self._pose = vision.PoseLandmarker.create_from_options(pose_options)
        self._hands = vision.HandLandmarker.create_from_options(hand_options)
        self._smoother = LandmarkSmoother()

    def close(self) -> None:
        self._pose.close()
        self._hands.close()

    def reset_session(self) -> None:
        self._smoother.reset()

    def process_jpeg(
        self,
        jpeg: bytes,
        timestamp_ms: int,
        frame_index: int,
    ) -> MotionFrameData | None:
        arr = cv2.imdecode(np.frombuffer(jpeg, dtype=np.uint8), cv2.IMREAD_COLOR)
        if arr is None:
            return None
        return self.process_bgr(arr, timestamp_ms, frame_index)

    def process_bgr(
        self,
        bgr: np.ndarray,
        timestamp_ms: int,
        frame_index: int,
    ) -> MotionFrameData | None:
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        pose_result = self._pose.detect_for_video(mp_image, timestamp_ms)
        if not pose_result.pose_landmarks:
            return None

        hand_result = self._hands.detect_for_video(mp_image, timestamp_ms)
        raw = build_motion_frame(pose_result.pose_landmarks[0], timestamp_ms, frame_index)
        raw = attach_hands(raw, extract_hands(hand_result))
        motion_frame = self._smoother.smooth(raw)

        if not is_tracking_reliable(motion_frame):
            return None

        return motion_frame
