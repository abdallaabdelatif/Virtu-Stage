import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app


def registration_payload(username: str, email: str) -> dict[str, str]:
    return {
        "username": username,
        "email": email,
        "password": "Strong@123",
        "first_name": "Test",
        "last_name": "User",
        "gender": "male",
    }


def test_register_rejects_invalid_username_before_crud_call(monkeypatch):
    called = False

    async def fake_create_user(_payload):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr("app.auth.routes.crud_client.create_user", fake_create_user)
    client = TestClient(app)
    response = client.post(
        "/api/auth/register",
        json=registration_payload("bad space", "valid@example.com"),
    )

    assert response.status_code == 422
    assert called is False


def test_register_normalizes_identity_before_crud_call(monkeypatch):
    captured = {}

    async def fake_create_user(payload):
        captured.update(payload)
        return {
            "user_id": "3fc9da6d-b6a4-4e95-99d0-3568a8bdce53",
            "username": payload["username"],
            "email": payload["email"],
            "first_name": payload["first_name"],
            "last_name": payload["last_name"],
            "gender": payload["gender"],
            "role": "user",
            "is_active": True,
            "created_at": "2026-06-28T00:00:00+00:00",
            "updated_at": "2026-06-28T00:00:00+00:00",
        }

    monkeypatch.setattr("app.auth.routes.crud_client.create_user", fake_create_user)
    client = TestClient(app)
    response = client.post(
        "/api/auth/register",
        json=registration_payload("  Valid.User  ", "Mixed.Email@Example.COM"),
    )

    assert response.status_code == 201
    assert captured["username"] == "Valid.User"
    assert captured["email"] == "mixed.email@example.com"
