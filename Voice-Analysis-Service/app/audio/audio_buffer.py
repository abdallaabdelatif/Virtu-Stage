# buffer used to accumulate raw PCM audio chunks for one session used by the audio socket

from __future__ import annotations
import io
import wave
from dataclasses import dataclass, field


SAMPLE_RATE_HZ = 16_000
SAMPLE_WIDTH_BYTES = 2  # 16-bit PCM
CHANNELS = 1  # mono


@dataclass
class AudioBuffer:
    session_id: str
    pcm_chunks: list[bytes] = field(default_factory=list)

    def add_chunk(self, pcm_bytes: bytes) -> None:
        self.pcm_chunks.append(pcm_bytes)

    @property
    def has_audio(self) -> bool:
        return len(self.pcm_chunks) > 0

    # pcm to wav happens once for whole audio when the session ends not per chunk
    def to_wav_bytes(self) -> bytes:
        raw_pcm = b"".join(self.pcm_chunks)
        buffer = io.BytesIO()  # creates an in-memory binary buffer
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(CHANNELS)
            wav_file.setsampwidth(SAMPLE_WIDTH_BYTES)
            wav_file.setframerate(SAMPLE_RATE_HZ)
            wav_file.writeframes(raw_pcm)
        return buffer.getvalue()
