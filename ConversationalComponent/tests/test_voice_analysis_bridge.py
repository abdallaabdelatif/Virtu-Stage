import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from voice_analysis_bridge import (  # noqa: E402
    build_transcript_ws_url,
    create_transcript_payload,
    resolve_session_id,
)


def test_build_transcript_ws_url_uses_session_id() -> None:
    url = build_transcript_ws_url("ws://localhost:8001", "session-123")
    assert url == "ws://localhost:8001/ws/voice-analysis/transcript/session-123"


def test_create_transcript_payload_formats_expected_message() -> None:
    payload = create_transcript_payload("hello world")
    assert json.loads(payload) == {"type": "transcript", "text": "hello world"}


def test_resolve_session_id_prefers_explicit_value() -> None:
    assert resolve_session_id({"session_id": "vr-session"}, "fallback") == "vr-session"
    assert resolve_session_id({}, "fallback") == "fallback"
