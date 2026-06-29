import sys
from pathlib import Path
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.api import vr as vr_module
from app.testing_allure import allure


INTERNAL_HEADERS = {"X-Internal-API-Key": "development-internal-key-change-me"}
AUTH_HEADERS = {"Authorization": "Bearer test-token"}


@pytest.fixture(autouse=True)
def fake_auth(monkeypatch):
    monkeypatch.setattr("app.main.verify_token", lambda token: {"sub": "test-user"})

    async def fake_get_user(user_id: str):
        return {"user_id": user_id, "role": "user", "is_active": True}

    async def fake_create_training_session(payload):
        return payload

    monkeypatch.setattr("app.main.crud_client.get_user", fake_get_user)
    monkeypatch.setattr(
        vr_module.crud_client, "create_training_session", fake_create_training_session
    )
    yield
    vr_module.session_store.clear()


@allure.feature("VR Session API")
@allure.story("Create VR session")
@allure.severity(allure.severity_level.CRITICAL)
def test_create_session():
    client = TestClient(app)
    session_id = str(uuid.uuid4())

    response = client.post(
        "/sessions",
        json={"session_id": session_id, "mode": 1, "job": "tester", "user_id": "test-user"},
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 201
    assert response.json() == {"session_id": session_id}


@allure.feature("VR Session API")
@allure.story("Authentication required")
@allure.severity(allure.severity_level.CRITICAL)
def test_create_session_requires_bearer_token():
    response = TestClient(app).post(
        "/sessions",
        json={"session_id": str(uuid.uuid4()), "mode": 1, "job": "tester"},
    )

    assert response.status_code == 401


@allure.feature("VR Session API")
@allure.story("Duplicate session protection")
@allure.severity(allure.severity_level.CRITICAL)
def test_create_session_duplicate():
    client = TestClient(app)
    session_id = str(uuid.uuid4())

    client.post(
        "/sessions",
        json={"session_id": session_id, "mode": 1, "job": "tester", "user_id": "test-user"},
        headers=AUTH_HEADERS,
    )
    response = client.post(
        "/sessions",
        json={"session_id": session_id, "mode": 1, "job": "tester", "user_id": "test-user"},
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 409


@allure.feature("Voice Analysis Integration")
@allure.story("Forward voice analysis result to CRUD")
@allure.severity(allure.severity_level.CRITICAL)
def test_ingest_voice_analysis_forwards_to_crud(monkeypatch):
    async def fake_create_voice_analysis(payload):
        return {"success": True, **payload}

    monkeypatch.setattr(vr_module.crud_client, "create_voice_analysis", fake_create_voice_analysis)

    client = TestClient(app)
    payload = {
        "session_id": str(uuid.uuid4()),
        "anxiety_level": 30.0,
        "confidence_level": 80.0,
        "clarity_level": 75.0,
        "focus_level": 70.0,
        "pause_ratio": 0.12,
        "pause_count": 5,
        "longest_pause_sec": 1.5,
        "filler_word_count": 3,
        "words_per_minute": 130.0,
    }

    response = client.post("/voice-analyses", json=payload, headers=INTERNAL_HEADERS)

    assert response.status_code == 201
    assert response.json()["success"] is True
    assert response.json()["session_id"] == payload["session_id"]


@allure.feature("Voice Analysis Integration")
@allure.story("Internal API key required")
@allure.severity(allure.severity_level.CRITICAL)
def test_ingest_voice_analysis_requires_internal_key():
    payload = {
        "session_id": str(uuid.uuid4()),
        "anxiety_level": 30.0,
        "confidence_level": 80.0,
        "clarity_level": 75.0,
        "focus_level": 70.0,
        "pause_ratio": 0.12,
        "pause_count": 5,
        "longest_pause_sec": 1.5,
        "filler_word_count": 3,
        "words_per_minute": 130.0,
    }

    response = TestClient(app).post("/voice-analyses", json=payload)

    assert response.status_code == 401


@allure.feature("Motion Analysis Integration")
@allure.story("Forward motion analysis result to CRUD")
@allure.severity(allure.severity_level.CRITICAL)
def test_ingest_motion_analysis_forwards_to_crud(monkeypatch):
    async def fake_create_motion_analysis(payload):
        return {"success": True, **payload}

    monkeypatch.setattr(
        vr_module.crud_client,
        "create_motion_analysis",
        fake_create_motion_analysis,
    )

    client = TestClient(app)
    payload = {
        "session_id": str(uuid.uuid4()),
        "head_stability_score": 82.0,
        "head_movement_variance": 0.2,
        "head_angle": 4.5,
        "head_avg_velocity": 0.7,
        "fidgeting_level": "low",
        "fidgeting_score": 88.0,
        "hand_movement_score": 79.0,
        "left_hand_avg_velocity": 0.6,
        "right_hand_avg_velocity": 0.8,
        "posture_quality": 84.0,
        "posture_score": 83.0,
        "nervousness_indicator": 18.0,
        "motion_overall_score": 82.0,
        "presentation_assessment": {"summary": "Stable posture"},
        "recommendations": ["Keep hands visible"],
        "dominant_posture_type": "upright",
        "session_metrics": {"frames_processed": 120},
    }

    response = client.post("/motion-analyses", json=payload, headers=INTERNAL_HEADERS)

    assert response.status_code == 201
    assert response.json()["success"] is True
    assert response.json()["session_id"] == payload["session_id"]


@allure.feature("Motion Analysis Integration")
@allure.story("Internal API key required")
@allure.severity(allure.severity_level.CRITICAL)
def test_ingest_motion_analysis_requires_internal_key():
    payload = {
        "session_id": str(uuid.uuid4()),
        "head_stability_score": 82.0,
        "head_movement_variance": 0.2,
        "head_angle": 4.5,
        "head_avg_velocity": 0.7,
        "fidgeting_level": "low",
        "fidgeting_score": 88.0,
        "hand_movement_score": 79.0,
        "left_hand_avg_velocity": 0.6,
        "right_hand_avg_velocity": 0.8,
        "posture_quality": 84.0,
        "posture_score": 83.0,
        "nervousness_indicator": 18.0,
        "motion_overall_score": 82.0,
    }

    response = TestClient(app).post("/motion-analyses", json=payload)

    assert response.status_code == 401


@allure.feature("VR Session API")
@allure.story("Invalid mode validation")
@allure.severity(allure.severity_level.CRITICAL)
def test_create_session_rejects_invalid_mode():
    response = TestClient(app).post(
        "/sessions",
        json={"session_id": str(uuid.uuid4()), "mode": 3, "job": "tester"},
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 422


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
