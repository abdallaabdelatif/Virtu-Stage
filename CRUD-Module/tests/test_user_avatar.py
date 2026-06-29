import pytest


INTERNAL_HEADERS = {"X-Internal-API-Key": "test-internal-key"}


@pytest.mark.asyncio
async def test_internal_avatar_update_is_persisted(client, user_id):
    avatar_key = f"avatars/{user_id}/19023b19-f5b1-4ac2-8041-eb74692f51e9.webp"

    response = await client.patch(
        f"/internal/users/{user_id}/avatar",
        json={"avatar_key": avatar_key},
        headers=INTERNAL_HEADERS,
    )

    assert response.status_code == 200
    assert response.json()["avatar_key"] == avatar_key

    fetched = await client.get(f"/users/{user_id}")
    assert fetched.status_code == 200
    assert fetched.json()["avatar_key"] == avatar_key


@pytest.mark.asyncio
async def test_internal_avatar_update_rejects_non_avatar_key(client, user_id):
    response = await client.patch(
        f"/internal/users/{user_id}/avatar",
        json={"avatar_key": "presentations/private.pdf"},
        headers=INTERNAL_HEADERS,
    )
    assert response.status_code == 422
