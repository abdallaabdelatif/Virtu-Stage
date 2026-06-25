from __future__ import annotations

import struct
from dataclasses import dataclass


@dataclass(frozen=True)
class VRFrame:
    index: int
    timestamp_ms: int
    jpeg: bytes


def decode_vr_frame_batch(data: bytes) -> list[VRFrame]:
    if len(data) < 4:
        raise ValueError("Frame batch too short")

    offset = 0
    (count,) = struct.unpack_from("<I", data, offset)
    offset += 4
    frames: list[VRFrame] = []

    for _ in range(count):
        if offset + 16 > len(data):
            raise ValueError("Truncated frame batch header")
        index, timestamp_ms, jpg_len = struct.unpack_from("<IqI", data, offset)
        offset += 16
        if offset + jpg_len > len(data):
            raise ValueError("Truncated JPEG payload")
        jpeg = data[offset : offset + jpg_len]
        offset += jpg_len
        frames.append(VRFrame(index=index, timestamp_ms=timestamp_ms, jpeg=jpeg))

    return frames
