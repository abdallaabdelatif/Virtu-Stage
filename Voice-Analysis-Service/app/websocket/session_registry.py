# tracks the state of a single session by holding the result of each analysis branch till both
# are ready to be merged and sent to the central backend
from __future__ import annotations
from dataclasses import dataclass
from app.schemas.result import AudioAnalysisResult, TranscriptAnalysisResult


@dataclass
class SessionState:
    audio_result: AudioAnalysisResult | None = None
    transcript_result: TranscriptAnalysisResult | None = None

    @property
    def both_results_ready(self) -> bool:
        return self.audio_result is not None and self.transcript_result is not None


class SessionRegistry:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}

    def get_or_create(self, session_id: str) -> SessionState:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionState()
        return self._sessions[session_id]

    def remove(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


# single shared instance used by both websocket handlers to store the results of a single session from both branches
session_registry = SessionRegistry()
