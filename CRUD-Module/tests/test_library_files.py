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

    processing = await client.patch(
        f"/files/{file_id}/processing",
        json={
            "processing_status": "processing",
            "slide_count": None,
            "processing_error": None,
            "processed_at": None,
        },
        headers=INTERNAL_HEADERS,
    )
    assert processing.status_code == 200
    assert processing.json()["processing_status"] == "processing"

    slides_payload = {
        "slides": [
            {
                "slide_number": number,
                "object_key": f"presentations/{user_id}/{file_id}/slides/{number:04d}.png",
                "width": 1920,
                "height": 1080,
                "size_bytes": 1000 + number,
            }
            for number in (1, 2)
        ]
    }
    replaced = await client.put(
        f"/files/{file_id}/slides",
        json=slides_payload,
        headers=INTERNAL_HEADERS,
    )
    assert replaced.status_code == 200
    assert [slide["slide_number"] for slide in replaced.json()] == [1, 2]

    slides = await client.get(
        f"/files/{file_id}/slides", headers=INTERNAL_HEADERS
    )
    assert slides.status_code == 200
    assert [slide["slide_number"] for slide in slides.json()] == [1, 2]

    ready = await client.get(f"/files/{file_id}", headers=INTERNAL_HEADERS)
    assert ready.json()["processing_status"] == "ready"
    assert ready.json()["slide_count"] == 2

    deleted = await client.delete(f"/files/{file_id}", headers=INTERNAL_HEADERS)
    assert deleted.status_code == 204
    missing = await client.get(f"/files/{file_id}", headers=INTERNAL_HEADERS)
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_slide_numbers_must_be_consecutive(client: AsyncClient, user_id: str):
    file_id = str(uuid.uuid4())
    await client.post(
        "/files",
        json={
            "file_id": file_id,
            "user_id": user_id,
            "original_name": "deck.pdf",
            "object_key": f"presentations/{user_id}/{file_id}/deck.pdf",
            "content_type": "application/pdf",
            "size_bytes": 100,
        },
        headers=INTERNAL_HEADERS,
    )
    response = await client.put(
        f"/files/{file_id}/slides",
        json={
            "slides": [
                {
                    "slide_number": 2,
                    "object_key": f"presentations/{user_id}/{file_id}/slides/0002.png",
                    "width": 1920,
                    "height": 1080,
                    "size_bytes": 100,
                }
            ]
        },
        headers=INTERNAL_HEADERS,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_library_file_endpoints_require_internal_key(
    client: AsyncClient, user_id: str
):
    response = await client.get(f"/files/user/{user_id}")
    assert response.status_code == 401
