import sys
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.testing_allure import allure


def registration_payload(username: str, email: str) -> dict[str, str]:
    return {
        "username": username,
        "email": email,
        "password": "Strong@123",
        "first_name": "Test",
        "last_name": "User",
        "gender": "male",
    }


@allure.feature("Authentication")
@allure.story("Invalid username validation")
@allure.severity(allure.severity_level.CRITICAL)
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


@allure.feature("Authentication")
@allure.story("Identity normalization")
@allure.severity(allure.severity_level.NORMAL)
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


@allure.feature("Authentication")
@allure.story("Weak password validation")
@allure.severity(allure.severity_level.CRITICAL)
def test_register_rejects_weak_password_before_crud_call(monkeypatch):
    called = False

    async def fake_create_user(_payload):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr("app.auth.routes.crud_client.create_user", fake_create_user)
    client = TestClient(app)
    response = client.post(
        "/api/auth/register",
        json={
            **registration_payload("validuser", "valid@example.com"),
            "password": "weak",
        },
    )

    assert response.status_code == 422
    assert called is False


@allure.feature("Authentication")
@allure.story("Duplicate email validation")
@allure.severity(allure.severity_level.CRITICAL)
def test_register_returns_duplicate_email_conflict_from_crud(monkeypatch):
    async def fake_create_user(_payload):
        request = httpx.Request("POST", "http://crud/users")
        response = httpx.Response(
            409,
            request=request,
            json={"detail": "An account with this email already exists"},
        )
        raise httpx.HTTPStatusError(
            "duplicate email",
            request=request,
            response=response,
        )

    monkeypatch.setattr("app.auth.routes.crud_client.create_user", fake_create_user)
    client = TestClient(app)
    response = client.post(
        "/api/auth/register",
        json=registration_payload("newuser", "duplicate@example.com"),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "An account with this email already exists"


@allure.feature("Authentication")
@allure.story("Duplicate username validation")
@allure.severity(allure.severity_level.CRITICAL)
def test_register_returns_duplicate_username_conflict_from_crud(monkeypatch):
    async def fake_create_user(_payload):
        request = httpx.Request("POST", "http://crud/users")
        response = httpx.Response(
            409,
            request=request,
            json={"detail": "Username is already taken"},
        )
        raise httpx.HTTPStatusError(
            "duplicate username",
            request=request,
            response=response,
        )

    monkeypatch.setattr("app.auth.routes.crud_client.create_user", fake_create_user)
    client = TestClient(app)
    response = client.post(
        "/api/auth/register",
        json=registration_payload("existinguser", "new@example.com"),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Username is already taken"


@allure.feature("Authentication")
@allure.story("Invalid login validation")
@allure.severity(allure.severity_level.CRITICAL)
def test_login_rejects_invalid_credentials(monkeypatch):
    async def fake_login_verify(_payload):
        request = httpx.Request("POST", "http://crud/internal/auth/login")
        response = httpx.Response(
            401,
            request=request,
            json={"detail": "Invalid credentials"},
        )
        raise httpx.HTTPStatusError(
            "invalid credentials",
            request=request,
            response=response,
        )

    monkeypatch.setattr("app.auth.routes.crud_client.login_verify", fake_login_verify)
    client = TestClient(app)
    response = client.post(
        "/api/auth/login",
        json={"username_or_email": "valid@example.com", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
