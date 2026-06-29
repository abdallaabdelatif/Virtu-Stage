import sys
import uuid
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.testing_allure import allure


AUTH_HEADERS = {"Authorization": "Bearer test-token"}


def _account_client(monkeypatch, avatar_key: str | None = None):
    user_id = str(uuid.uuid4())
    user = {
        "user_id": user_id,
        "username": "postman_user",
        "email": "postman@example.com",
        "first_name": "Postman",
        "last_name": "Tester",
        "gender": "male",
        "role": "user",
        "is_active": True,
        "avatar_key": avatar_key,
        "created_at": "2026-06-28T00:00:00+00:00",
        "updated_at": "2026-06-28T00:00:00+00:00",
    }

    async def fake_get_user(_user_id: str):
        return user

    monkeypatch.setattr("app.main.verify_token", lambda _token: {"sub": user_id})
    monkeypatch.setattr("app.main.crud_client.get_user", fake_get_user)
    return TestClient(app), user


@allure.feature("Protected Routes")
@allure.story("Protected route returns authenticated user")
@allure.severity(allure.severity_level.CRITICAL)
def test_protected_route_returns_current_user(monkeypatch):
    client, user = _account_client(monkeypatch)

    response = client.get("/protected", headers=AUTH_HEADERS)

    assert response.status_code == 200
    assert response.json() == {
        "message": "authorized",
        "user_id": user["user_id"],
        "username": user["username"],
    }


@allure.feature("Protected Routes")
@allure.story("Bearer token is required")
@allure.severity(allure.severity_level.CRITICAL)
def test_protected_route_requires_token():
    response = TestClient(app).get("/protected")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@allure.feature("Account Management")
@allure.story("Update profile")
@allure.severity(allure.severity_level.NORMAL)
def test_update_profile_forwards_to_crud(monkeypatch):
    client, user = _account_client(monkeypatch)
    captured = {}

    async def fake_update_profile(user_id: str, first_name: str, last_name: str):
        captured.update(
            {
                "user_id": user_id,
                "first_name": first_name,
                "last_name": last_name,
            }
        )
        return {
            **user,
            "first_name": first_name,
            "last_name": last_name,
        }

    monkeypatch.setattr(
        "app.api.account.crud_client.update_user_profile",
        fake_update_profile,
    )

    response = client.patch(
        "/api/users/me",
        headers=AUTH_HEADERS,
        json={"first_name": "Updated", "last_name": "Name"},
    )

    assert response.status_code == 200
    assert response.json()["first_name"] == "Updated"
    assert captured == {
        "user_id": user["user_id"],
        "first_name": "Updated",
        "last_name": "Name",
    }


@allure.feature("Account Management")
@allure.story("Change password rejects invalid current password")
@allure.severity(allure.severity_level.CRITICAL)
def test_change_password_rejects_invalid_current_password(monkeypatch):
    client, _user = _account_client(monkeypatch)

    async def fake_change_password(_user_id: str, _current: str, _new: str):
        request = httpx.Request("PATCH", "http://crud/internal/auth/change-password")
        response = httpx.Response(
            401,
            request=request,
            json={"detail": "Current password is incorrect"},
        )
        raise httpx.HTTPStatusError(
            "invalid password",
            request=request,
            response=response,
        )

    monkeypatch.setattr(
        "app.api.account.crud_client.change_password",
        fake_change_password,
    )

    response = client.patch(
        "/api/users/me/password",
        headers=AUTH_HEADERS,
        json={
            "current_password": "WrongPass123!",
            "new_password": "NewPass123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Current password is incorrect"


@allure.feature("Account Management")
@allure.story("Delete account cleans up avatar")
@allure.severity(allure.severity_level.CRITICAL)
def test_delete_account_removes_user_and_avatar(monkeypatch):
    avatar_key = f"avatars/{uuid.uuid4()}/{uuid.uuid4()}.webp"
    client, user = _account_client(monkeypatch, avatar_key=avatar_key)
    deleted_users = []
    deleted_avatars = []

    async def fake_delete_user(user_id: str):
        deleted_users.append(user_id)

    async def fake_delete_avatar(object_key: str):
        deleted_avatars.append(object_key)

    monkeypatch.setattr("app.api.account.crud_client.delete_user", fake_delete_user)
    monkeypatch.setattr("app.api.account.file_storage.delete_avatar", fake_delete_avatar)

    response = client.delete("/api/users/me", headers=AUTH_HEADERS)

    assert response.status_code == 204
    assert deleted_users == [user["user_id"]]
    assert deleted_avatars == [avatar_key]

