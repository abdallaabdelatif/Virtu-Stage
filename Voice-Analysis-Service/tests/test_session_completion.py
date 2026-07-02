from __future__ import annotations

import importlib
import sys
import types

import pytest


@pytest.fixture
def session_completion(monkeypatch):
    pipeline_stub = types.ModuleType("app.analysis.pipeline")

    async def analyze_audio_buffer(_buffer):
        return {}

    async def analyze_transcript_buffer(_buffer, **_kwargs):
        return {}

    pipeline_stub.analyze_audio_buffer = analyze_audio_buffer
    pipeline_stub.analyze_transcript_buffer = analyze_transcript_buffer
    monkeypatch.setitem(sys.modules, "app.analysis.pipeline", pipeline_stub)
    sys.modules.pop("app.websocket.session_completion", None)

    module = importlib.import_module("app.websocket.session_completion")
    module._session_results.clear()
    monkeypatch.setattr(
        module,
        "VOICE_ANALYSIS_RESULT_CALLBACK_URL",
        "http://central-backend.railway.internal:8080/voice-analyses",
    )
    return module


def test_flat_result_payload_preserves_trait_reasons(session_completion):
    reasons = {
        "confidence_level": ["Stable energy supports this score."],
        "anxiety_level": ["Low pause pressure keeps anxiety evidence low."],
        "clarity_level": ["Articulation supports this score."],
        "focus_level": ["Topic consistency supports this score."],
    }

    payload = session_completion._flat_result_payload(
        session_id="session-reasons",
        analysis={"trait_reasons": reasons},
        feedback={},
    )

    assert payload["confidence_reasons"] == reasons["confidence_level"]
    assert payload["anxiety_reasons"] == reasons["anxiety_level"]
    assert payload["clarity_reasons"] == reasons["clarity_level"]
    assert payload["focus_reasons"] == reasons["focus_level"]


@pytest.mark.asyncio
async def test_configured_callback_is_registered_and_used(
    session_completion,
    monkeypatch,
):
    session_id = "session-123"
    await session_completion.register_result_callback(session_id)
    state = session_completion._session_results[session_id]
    state.audio_closed = True
    state.transcript_closed = True
    state.audio_done.set()
    state.transcript_done.set()

    callbacks: list[tuple[str, dict]] = []

    async def post_result(callback_url: str, payload: dict) -> bool:
        callbacks.append((callback_url, payload))
        return True

    monkeypatch.setattr(session_completion.result_sender, "post_result", post_result)

    assert await session_completion.send_result_if_ready(session_id) is True
    assert callbacks[0][0] == (
        "http://central-backend.railway.internal:8080/voice-analyses"
    )
    assert callbacks[0][1]["session_id"] == session_id
    assert state.result_sent is True
    assert state.result_sending is False


@pytest.mark.asyncio
async def test_failed_callback_is_not_marked_as_sent(
    session_completion,
    monkeypatch,
):
    session_id = "session-456"
    await session_completion.register_result_callback(session_id)
    state = session_completion._session_results[session_id]
    state.audio_closed = True
    state.transcript_closed = True
    state.audio_done.set()
    state.transcript_done.set()

    async def post_result(_callback_url: str, _payload: dict) -> bool:
        return False

    monkeypatch.setattr(session_completion.result_sender, "post_result", post_result)

    assert await session_completion.send_result_if_ready(session_id) is False
    assert state.result_sent is False
    assert state.result_sending is False
    assert state.errors == [
        "result_callback_failed: "
        "http://central-backend.railway.internal:8080/voice-analyses"
    ]
