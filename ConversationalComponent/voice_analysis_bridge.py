import json


def build_transcript_ws_url(base_url: str, session_id: str) -> str:
    normalized_base = base_url.rstrip("/")
    return f"{normalized_base}/ws/internal/voice-analysis/transcript/{session_id}"


def create_transcript_payload(text: str) -> str:
    return json.dumps({"type": "transcript", "text": text})


def resolve_session_id(message_data: dict, fallback_session_id: str) -> str:
    session_id = message_data.get("session_id") or message_data.get("sessionId")
    return session_id or fallback_session_id
