import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.routers.user import create_user
from app.schemas.user import UserCreate


def registration_payload(username: str, email: str) -> dict[str, str]:
    return {
        "username": username,
        "email": email,
        "password": "Strong@123",
        "first_name": "Test",
        "last_name": "User",
        "gender": "male",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "username",
    ["ab", "bad space", "-invalid", "a" * 31],
)
async def test_registration_rejects_invalid_username(client, username):
    response = await client.post(
        "/users", json=registration_payload(username, "valid@example.com")
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_registration_normalizes_email_and_rejects_case_variants(client):
    created = await client.post(
        "/users", json=registration_payload("Case.User", "Mixed.Email@Example.COM")
    )
    assert created.status_code == 201
    assert created.json()["email"] == "mixed.email@example.com"

    username_login = await client.post(
        "/internal/auth/login",
        json={"username_or_email": "CASE.USER", "password": "Strong@123"},
        headers={"X-Internal-API-Key": "test-internal-key"},
    )
    assert username_login.status_code == 200

    email_login = await client.post(
        "/internal/auth/login",
        json={
            "username_or_email": "MIXED.EMAIL@EXAMPLE.COM",
            "password": "Strong@123",
        },
        headers={"X-Internal-API-Key": "test-internal-key"},
    )
    assert email_login.status_code == 200

    duplicate_username = await client.post(
        "/users", json=registration_payload("case.user", "other@example.com")
    )
    assert duplicate_username.status_code == 409
    assert duplicate_username.json()["detail"] == "Username is already taken"

    duplicate_email = await client.post(
        "/users", json=registration_payload("other.user", "MIXED.EMAIL@example.com")
    )
    assert duplicate_email.status_code == 409
    assert duplicate_email.json()["detail"] == "An account with this email already exists"


@pytest.mark.asyncio
async def test_commit_race_returns_controlled_conflict():
    class RaceSession:
        def __init__(self):
            self.scalar_results = [None, None, "existing-user-id"]
            self.rolled_back = False

        async def scalar(self, _statement):
            return self.scalar_results.pop(0)

        def add(self, _user):
            return None

        async def commit(self):
            raise IntegrityError("insert user", {}, Exception("unique conflict"))

        async def rollback(self):
            self.rolled_back = True

    race_session = RaceSession()
    payload = UserCreate(**registration_payload("race.user", "race@example.com"))

    with pytest.raises(HTTPException) as exc_info:
        await create_user(payload, race_session)

    assert race_session.rolled_back is True
    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Username is already taken"
