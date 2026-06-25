import sys
from pathlib import Path
import json
from unittest.mock import AsyncMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.clients.conversational_proxy import ConversationalProxy
from app.clients.voice_analysis_proxy import VoiceAnalysisProxy


@pytest.mark.asyncio
async def test_conversational_proxy_connects_and_forwards(monkeypatch):
    dummy_ws = AsyncMock()
    monkeypatch.setattr(
        "app.clients.conversational_proxy.websockets.connect",
        AsyncMock(return_value=dummy_ws),
    )

    proxy = ConversationalProxy("session-123", mode=1, job="interview")
    await proxy.connect()

    dummy_ws.send.assert_any_await(json.dumps({"type": "set_mode", "mode": 1}))
    dummy_ws.send.assert_any_await(json.dumps({"type": "set_job", "job": "interview"}))

    await proxy.send_bytes(b"\x00\x01")
    dummy_ws.send.assert_awaited_with(b"\x00\x01")

    dummy_ws.recv.return_value = b"\x02\x03"
    received = await proxy.receive_message()
    assert received == b"\x02\x03"

    await proxy.close()
    dummy_ws.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_voice_analysis_proxy_connect_url(monkeypatch):
    dummy_ws = AsyncMock()
    connect_mock = AsyncMock(return_value=dummy_ws)
    monkeypatch.setattr("app.clients.voice_analysis_proxy.websockets.connect", connect_mock)

    proxy = VoiceAnalysisProxy("session-456")
    await proxy.connect()

    connect_mock.assert_awaited_once_with("ws://localhost:8001/ws/voice-analysis/audio/session-456")
    await proxy.close()
    dummy_ws.close.assert_awaited_once()
