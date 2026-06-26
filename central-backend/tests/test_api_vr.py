import sys
from pathlib import Path
import uuid

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.api import vr as vr_module


@pytest.fixture(autouse=True)
def fake_auth(monkeypatch):
    monkeypatch.setattr("app.main.verify_token", lambda token: {"sub": "test-user"})

    async def fake_get_user(user_id: str):
        return {"user_id": user_id}

    monkeypatch.setattr("app.main.crud_client.get_user", fake_get_user)
    yield
    vr_module.session_store.clear()


def test_create_session():
    client = TestClient(app)
    session_id = str(uuid.uuid4())

    response = client.post(
        "/sessions",
        json={"session_id": session_id, "mode": 1, "job": "tester", "user_id": "test-user"},
    )

    assert response.status_code == 201
    assert response.json() == {"session_id": session_id}


def test_create_session_duplicate():
    client = TestClient(app)
    session_id = str(uuid.uuid4())

    client.post(
        "/sessions",
        json={"session_id": session_id, "mode": 1, "job": "tester", "user_id": "test-user"},
    )
    response = client.post(
        "/sessions",
        json={"session_id": session_id, "mode": 1, "job": "tester", "user_id": "test-user"},
    )

    assert response.status_code == 409


def test_ingest_voice_analysis_forwards_to_crud(monkeypatch):
    async def fake_create_voice_analysis(payload):
        return {"success": True, **payload}

    monkeypatch.setattr(vr_module.crud_client, "create_voice_analysis", fake_create_voice_analysis)

    client = TestClient(app)
    payload = {
        "session_id": str(uuid.uuid4()),
        "emotions": {"neutral": 0.25, "happy": 0.25, "sad": 0.25, "angry": 0.25},
        "anxiety_level": 0.3,
        "confidence_score": 0.8,
        "clarity_level": 0.75,
        "focus_score": 0.7,
    }

    response = client.post("/voice-analyses", json=payload)

    assert response.status_code == 201
    assert response.json()["success"] is True
    assert response.json()["session_id"] == payload["session_id"]


def test_cleanup_session_waits_for_other_streams_to_finish():
    session_id = str(uuid.uuid4())
    vr_module.session_store[session_id] = {
        "mode": 1,
        "job": "tester",
        "user_id": "test-user",
        "active_streams": {"audio": True, "frames": True},
        "voice_proxy": None,
        "conv_proxy": None,
        "motion_proxy": None,
    }

    vr_module._cleanup_session(session_id)

    assert session_id in vr_module.session_store


def test_cleanup_session_removes_when_no_streams_are_active():
    session_id = str(uuid.uuid4())
    vr_module.session_store[session_id] = {
        "mode": 1,
        "job": "tester",
        "user_id": "test-user",
        "active_streams": {"audio": False, "frames": False},
        "voice_proxy": None,
        "conv_proxy": None,
        "motion_proxy": None,
    }

    vr_module._cleanup_session(session_id)

    assert session_id not in vr_module.session_store
