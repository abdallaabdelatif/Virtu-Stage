import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app


@pytest.fixture
def admin_client(monkeypatch):
    admin_id = str(uuid.uuid4())

    async def fake_get_user(user_id: str):
        return {
            "user_id": user_id,
            "role": "admin" if user_id == admin_id else "user",
            "is_active": True,
        }

    dashboard_payload = {
        "total_users": 2,
        "total_sessions": 5,
        "platform_average_score": 78.0,
        "sessions_today": 1,
        "sessions_by_day": [{"date": "2026-06-28", "count": 1}],
        "average_score_by_month": [{"month": "2026-06", "score": 78.0}],
        "recent_registrations": [
            {
                "user_id": str(uuid.uuid4()),
                "name": "Sara Ahmed",
                "email": "sara@example.com",
                "created_at": "2026-06-28T09:00:00+00:00",
            }
        ],
    }

    users_payload = [
        {
            "user_id": str(uuid.uuid4()),
            "name": "Sara Ahmed",
            "email": "sara@example.com",
            "role": "user",
            "is_active": True,
            "session_count": 3,
            "created_at": "2026-06-28T09:00:00+00:00",
        }
    ]

    user_dashboard_payload = {
        "total_sessions": 2,
        "analyzed_sessions": 1,
        "average_overall_score": 81.0,
        "improvement_rate": None,
        "score_history": [
            {
                "session_id": str(uuid.uuid4()),
                "date": "2026-06-28",
                "score": 81.0,
            }
        ],
        "analysis_history": [],
    }

    async def fake_get_user_dashboard(user_id: str):
        return user_dashboard_payload

    async def fake_get_admin_dashboard():
        return dashboard_payload

    async def fake_list_admin_users():
        return users_payload

    monkeypatch.setattr("app.main.verify_token", lambda token: {"sub": admin_id})
    monkeypatch.setattr("app.main.crud_client.get_user", fake_get_user)
    monkeypatch.setattr(
        "app.api.dashboard.crud_client.get_user_dashboard",
        fake_get_user_dashboard,
    )
    monkeypatch.setattr(
        "app.api.admin.crud_client.get_admin_dashboard",
        fake_get_admin_dashboard,
    )
    monkeypatch.setattr(
        "app.api.admin.crud_client.list_admin_users",
        fake_list_admin_users,
    )

    return TestClient(app), admin_id


def test_user_dashboard_endpoint(admin_client):
    client, admin_id = admin_client
    response = client.get(
        "/api/dashboard/me",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    assert response.json()["total_sessions"] == 2


def test_admin_dashboard_endpoint(admin_client):
    client, _ = admin_client
    response = client.get(
        "/api/admin/dashboard",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["sessions_today"] == 1
    assert body["platform_average_score"] == 78.0


def test_admin_users_endpoint(admin_client):
    client, _ = admin_client
    response = client.get(
        "/api/admin/users",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["session_count"] == 3


def test_admin_can_delete_regular_user(admin_client, monkeypatch):
    client, _ = admin_client
    target_id = client.get(
        "/api/admin/users",
        headers={"Authorization": "Bearer test-token"},
    ).json()[0]["user_id"]
    deleted_ids = []

    async def fake_delete_user(user_id: str):
        deleted_ids.append(user_id)

    monkeypatch.setattr(
        "app.api.admin.crud_client.delete_user",
        fake_delete_user,
    )

    response = client.delete(
        f"/api/admin/users/{target_id}",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 204
    assert deleted_ids == [target_id]


def test_admin_cannot_delete_self(admin_client, monkeypatch):
    client, admin_id = admin_client

    async def fail_if_called(_user_id: str):
        raise AssertionError("CRUD delete should not be called")

    monkeypatch.setattr(
        "app.api.admin.crud_client.delete_user",
        fail_if_called,
    )

    response = client.delete(
        f"/api/admin/users/{admin_id}",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Administrators cannot delete their own account"
    )
