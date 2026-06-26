import json
import os
from urllib.parse import urljoin


def build_transcript_ws_url(base_url: str, session_id: str) -> str:
    normalized_base = base_url.rstrip("/")
    return f"{normalized_base}/ws/voice-analysis/transcript/{session_id}"


def create_transcript_payload(text: str) -> str:
    return json.dumps({"type": "transcript", "text": text})


def resolve_session_id(message_data: dict, fallback_session_id: str) -> str:
    session_id = message_data.get("session_id") or message_data.get("sessionId")
    return session_id or fallback_session_id


def get_voice_analysis_ws_url(settings: object) -> str:
    base_url = getattr(settings, "VOICE_ANALYSIS_WS_URL", "ws://localhost:8001")
    session_id = getattr(settings, "VOICE_ANALYSIS_SESSION_ID", "")
    if session_id:
        return build_transcript_ws_url(base_url, session_id)
    return base_url
