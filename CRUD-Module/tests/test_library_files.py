import uuid

import pytest
from httpx import AsyncClient

from conftest import INTERNAL_HEADERS


@pytest.mark.asyncio
async def test_library_file_crud_is_scoped_by_user(
    client: AsyncClient, user_id: str
):
    file_id = str(uuid.uuid4())
    payload = {
        "file_id": file_id,
        "user_id": user_id,
        "original_name": "Quarterly Review.pdf",
        "object_key": f"presentations/{user_id}/{file_id}/Quarterly_Review.pdf",
        "content_type": "application/pdf",
        "size_bytes": 2048,
        "upload_status": "ready",
    }

    created = await client.post("/files", json=payload, headers=INTERNAL_HEADERS)
    assert created.status_code == 201
    assert created.json()["file_id"] == file_id

    listed = await client.get(
        f"/files/user/{user_id}", headers=INTERNAL_HEADERS
    )
    assert listed.status_code == 200
    assert [item["file_id"] for item in listed.json()] == [file_id]

    other_user = str(uuid.uuid4())
    empty_list = await client.get(
        f"/files/user/{other_user}", headers=INTERNAL_HEADERS
    )
    assert empty_list.status_code == 200
    assert empty_list.json() == []

    fetched = await client.get(f"/files/{file_id}", headers=INTERNAL_HEADERS)
    assert fetched.status_code == 200
    assert fetched.json()["object_key"] == payload["object_key"]

    deleted = await client.delete(f"/files/{file_id}", headers=INTERNAL_HEADERS)
    assert deleted.status_code == 204
    missing = await client.get(f"/files/{file_id}", headers=INTERNAL_HEADERS)
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_library_file_endpoints_require_internal_key(
    client: AsyncClient, user_id: str
):
    response = await client.get(f"/files/user/{user_id}")
    assert response.status_code == 401
