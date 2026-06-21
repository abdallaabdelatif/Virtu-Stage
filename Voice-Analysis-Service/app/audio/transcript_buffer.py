# buffer to accumulate text for a single sessoin used by the transcript socket

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class TranscriptBuffer:
    session_id: str
    fragments: list[str] = field(default_factory=list)

    def add_fragment(self, text: str) -> None:
        self.fragments.append(text)

    @property
    def has_text(self) -> bool:
        return len(self.fragments) > 0

    def full_transcript(self) -> str:
        return " ".join(self.fragments).strip()
