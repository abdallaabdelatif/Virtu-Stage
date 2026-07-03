import sys
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.services import session_report as report_service


@pytest.fixture
def client(monkeypatch):
    owner_id = str(uuid.uuid4())
    other_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())

    session_record = {
        "session_id": session_id,
        "user_id": owner_id,
        "scenario_type": "interview",
        "difficulty_level": "medium",
        "status": "processing",
        "start_time": datetime.now(timezone.utc).isoformat(),
        "end_time": datetime.now(timezone.utc).isoformat(),
        "overall_score": None,
        "voice_analysis_score": None,
        "motion_analysis_score": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    voice_record = {
        "anxiety_level": 20.0,
        "confidence_level": 82.0,
        "clarity_level": 79.0,
        "focus_level": 85.0,
        "pause_ratio": 0.12,
        "pause_count": 8,
        "longest_pause_sec": 2.4,
        "filler_word_count": 5,
        "words_per_minute": 137.0,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }

    async def fake_get_user(user_id: str):
        role = "admin" if user_id == "admin-user" else "user"
        return {
            "user_id": user_id,
            "role": role,
            "is_active": True,
        }

    async def fake_list_sessions(user_id: str):
        if user_id == owner_id:
            return [session_record]
        return []

    async def fake_get_session(sid: str):
        if sid == session_id:
            return session_record
        return None

    async def fake_get_voice(sid: str):
        if sid == session_id:
            return voice_record
        return None

    async def fake_get_motion(sid: str):
        return None

    monkeypatch.setattr("app.main.verify_token", lambda token: {"sub": owner_id})
    monkeypatch.setattr("app.main.crud_client.get_user", fake_get_user)
    monkeypatch.setattr(
        "app.api.sessions.crud_client.list_training_sessions_by_user",
        fake_list_sessions,
    )
    monkeypatch.setattr(
        "app.api.sessions.crud_client.get_training_session", fake_get_session
    )
    monkeypatch.setattr(
        "app.api.sessions.crud_client.get_voice_analysis_by_session", fake_get_voice
    )
    monkeypatch.setattr(
        "app.api.sessions.crud_client.get_motion_analysis_by_session", fake_get_motion
    )

    return TestClient(app), owner_id, other_id, session_id


def test_list_my_sessions(client):
    test_client, owner_id, _, _ = client
    response = test_client.get(
        "/api/sessions/me",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == "processing"


def test_list_my_sessions_resolves_timed_out_processing_status(client, monkeypatch):
    test_client, owner_id, _, session_id = client
    old_end = datetime.now(timezone.utc) - timedelta(seconds=700)
    old_session = {
        "session_id": session_id,
        "user_id": owner_id,
        "scenario_type": "interview",
        "difficulty_level": "medium",
        "status": "processing",
        "start_time": old_end.isoformat(),
        "end_time": old_end.isoformat(),
        "overall_score": None,
        "voice_analysis_score": 81.0,
        "motion_analysis_score": None,
        "created_at": old_end.isoformat(),
    }

    async def fake_list_sessions(_user_id: str):
        return [old_session]

    import app.api.sessions as sessions_module

    monkeypatch.setattr(
        sessions_module.crud_client,
        "list_training_sessions_by_user",
        fake_list_sessions,
    )
    monkeypatch.setattr(report_service, "ANALYSIS_TIMEOUT_SECONDS", 600)

    response = test_client.get(
        "/api/sessions/me",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.json()[0]["status"] == "failed"


def test_session_ownership_forbidden(client):
    test_client, _, other_id, session_id = client

    async def fake_get_user(user_id: str):
        return {"user_id": other_id, "role": "user", "is_active": True}

    import app.main as main_module

    main_module.crud_client.get_user = fake_get_user

    response = test_client.get(
        f"/api/sessions/{session_id}",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 403


def test_partial_report_voice_first(client, monkeypatch):
    test_client, owner_id, _, session_id = client
    monkeypatch.setattr(report_service, "ANALYSIS_TIMEOUT_SECONDS", 600)

    response = test_client.get(
        f"/api/sessions/{session_id}/report",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["report_status"] == "processing"
    assert body["voice_status"] == "ready"
    assert body["motion_status"] == "pending"
    assert body["voice_analysis"] is not None
    assert body["motion_analysis"] is None


def test_status_stays_processing_before_analysis_timeout(client, monkeypatch):
    test_client, _, _, session_id = client
    monkeypatch.setattr(report_service, "ANALYSIS_TIMEOUT_SECONDS", 600)

    response = test_client.get(
        f"/api/sessions/{session_id}/status",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "processing"


def test_status_fails_after_analysis_timeout(client, monkeypatch):
    test_client, owner_id, _, session_id = client
    old_end = datetime.now(timezone.utc) - timedelta(seconds=700)

    async def fake_get_session(_sid: str):
        return {
            "session_id": session_id,
            "user_id": owner_id,
            "scenario_type": "interview",
            "difficulty_level": "medium",
            "status": "processing",
            "start_time": old_end.isoformat(),
            "end_time": old_end.isoformat(),
            "overall_score": None,
            "voice_analysis_score": 81.0,
            "motion_analysis_score": None,
            "created_at": old_end.isoformat(),
        }

    import app.api.sessions as sessions_module

    sessions_module.crud_client.get_training_session = fake_get_session
    monkeypatch.setattr(report_service, "ANALYSIS_TIMEOUT_SECONDS", 600)

    response = test_client.get(
        f"/api/sessions/{session_id}/status",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "session_id": session_id,
        "status": "failed",
        "voice_ready": True,
        "motion_ready": False,
    }


def test_status_completes_when_both_callbacks_exist(client):
    test_client, _, _, session_id = client

    async def fake_get_motion(_sid: str):
        return {"session_id": session_id}

    import app.api.sessions as sessions_module

    sessions_module.crud_client.get_motion_analysis_by_session = fake_get_motion

    response = test_client.get(
        f"/api/sessions/{session_id}/status",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_partial_report_after_motion_timeout(client, monkeypatch):
    test_client, owner_id, _, session_id = client
    old_end = datetime.now(timezone.utc) - timedelta(seconds=700)

    async def fake_get_session(sid: str):
        return {
            "session_id": session_id,
            "user_id": owner_id,
            "scenario_type": "interview",
            "difficulty_level": "medium",
            "status": "processing",
            "start_time": old_end.isoformat(),
            "end_time": old_end.isoformat(),
            "overall_score": None,
            "voice_analysis_score": 81.0,
            "motion_analysis_score": None,
            "created_at": old_end.isoformat(),
        }

    import app.api.sessions as sessions_module

    sessions_module.crud_client.get_training_session = fake_get_session
    monkeypatch.setattr(report_service, "ANALYSIS_TIMEOUT_SECONDS", 600)

    response = test_client.get(
        f"/api/sessions/{session_id}/report",
        headers={"Authorization": "Bearer test-token"},
    )
    body = response.json()
    assert body["report_status"] == "partial"
    assert body["voice_status"] == "ready"
    assert body["motion_status"] == "failed"


def test_partial_report_motion_first(client, monkeypatch):
    test_client, owner_id, _, session_id = client
    monkeypatch.setattr(report_service, "ANALYSIS_TIMEOUT_SECONDS", 600)

    motion_record = {
        "head_stability_score": 0.82,
        "fidgeting_level": "low",
        "fidgeting_score": 0.12,
        "hand_movement_score": 74.0,
        "posture_quality": 80.0,
        "posture_score": 80.0,
        "nervousness_indicator": 18.0,
        "motion_overall_score": 76.0,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }

    async def fake_get_voice(_sid: str):
        return None

    async def fake_get_motion(sid: str):
        if sid == session_id:
            return motion_record
        return None

    import app.api.sessions as sessions_module

    sessions_module.crud_client.get_voice_analysis_by_session = fake_get_voice
    sessions_module.crud_client.get_motion_analysis_by_session = fake_get_motion

    response = test_client.get(
        f"/api/sessions/{session_id}/report",
        headers={"Authorization": "Bearer test-token"},
    )
    body = response.json()
    assert body["report_status"] == "processing"
    assert body["voice_status"] == "pending"
    assert body["motion_status"] == "ready"
    assert body["voice_analysis"] is None
    assert body["motion_analysis"] is not None


def test_complete_report(client, monkeypatch):
    test_client, owner_id, _, session_id = client
    monkeypatch.setattr(report_service, "ANALYSIS_TIMEOUT_SECONDS", 600)

    motion_record = {
        "head_stability_score": 0.82,
        "fidgeting_level": "low",
        "fidgeting_score": 0.12,
        "hand_movement_score": 74.0,
        "posture_quality": 80.0,
        "posture_score": 80.0,
        "nervousness_indicator": 18.0,
        "motion_overall_score": 76.0,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }

    async def fake_get_session(sid: str):
        return {
            "session_id": session_id,
            "user_id": owner_id,
            "scenario_type": "interview",
            "difficulty_level": "medium",
            "status": "completed",
            "start_time": datetime.now(timezone.utc).isoformat(),
            "end_time": datetime.now(timezone.utc).isoformat(),
            "overall_score": 78.75,
            "voice_analysis_score": 81.5,
            "motion_analysis_score": 76.0,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    async def fake_get_motion(sid: str):
        if sid == session_id:
            return motion_record
        return None

    import app.api.sessions as sessions_module

    sessions_module.crud_client.get_training_session = fake_get_session
    sessions_module.crud_client.get_motion_analysis_by_session = fake_get_motion

    response = test_client.get(
        f"/api/sessions/{session_id}/report",
        headers={"Authorization": "Bearer test-token"},
    )
    body = response.json()
    assert body["report_status"] == "complete"
    assert body["voice_status"] == "ready"
    assert body["motion_status"] == "ready"
    assert body["voice_analysis"] is not None
    assert body["motion_analysis"] is not None


def test_failed_report_when_both_analyses_timeout(client, monkeypatch):
    test_client, owner_id, _, session_id = client
    old_end = datetime.now(timezone.utc) - timedelta(seconds=700)

    async def fake_get_session(sid: str):
        return {
            "session_id": session_id,
            "user_id": owner_id,
            "scenario_type": "interview",
            "difficulty_level": "medium",
            "status": "processing",
            "start_time": old_end.isoformat(),
            "end_time": old_end.isoformat(),
            "overall_score": None,
            "voice_analysis_score": None,
            "motion_analysis_score": None,
            "created_at": old_end.isoformat(),
        }

    async def fake_get_voice(_sid: str):
        return None

    async def fake_get_motion(_sid: str):
        return None

    import app.api.sessions as sessions_module

    sessions_module.crud_client.get_training_session = fake_get_session
    sessions_module.crud_client.get_voice_analysis_by_session = fake_get_voice
    sessions_module.crud_client.get_motion_analysis_by_session = fake_get_motion
    monkeypatch.setattr(report_service, "ANALYSIS_TIMEOUT_SECONDS", 600)

    response = test_client.get(
        f"/api/sessions/{session_id}/report",
        headers={"Authorization": "Bearer test-token"},
    )
    body = response.json()
    assert body["report_status"] == "failed"
    assert body["voice_status"] == "failed"
    assert body["motion_status"] == "failed"
