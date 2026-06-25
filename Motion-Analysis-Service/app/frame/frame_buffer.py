from __future__ import annotations

from app.frame.vr_batch import VRFrame, decode_vr_frame_batch


class FrameBuffer:
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self._frames: list[VRFrame] = []

    def add_batch(self, data: bytes) -> None:
        self._frames.extend(decode_vr_frame_batch(data))

    @property
    def has_frames(self) -> bool:
        return bool(self._frames)

    @property
    def frames(self) -> list[VRFrame]:
        return list(self._frames)
