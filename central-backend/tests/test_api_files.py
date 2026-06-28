import io
import uuid
import zipfile
from datetime import datetime, timezone

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def file_api(monkeypatch):
    owner_id = str(uuid.uuid4())
    records: dict[str, dict] = {}
    uploaded: dict[str, bytes] = {}

    async def fake_get_user(user_id: str):
        return {"user_id": user_id, "role": "user", "is_active": True}

    async def fake_upload(file_object, object_key: str, content_type: str):
        uploaded[object_key] = file_object.read()

    async def fake_delete(object_key: str):
        uploaded.pop(object_key, None)

    async def fake_download_url(object_key: str):
        return f"https://signed.example/{object_key}?expires=300"

    async def fake_create(payload: dict):
        record = {
            **payload,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        records[payload["file_id"]] = record
        return record

    async def fake_list(user_id: str):
        return [record for record in records.values() if record["user_id"] == user_id]

    async def fake_get(file_id: str):
        return records.get(file_id)

    async def fake_delete_metadata(file_id: str):
        records.pop(file_id, None)

    monkeypatch.setattr("app.main.verify_token", lambda token: {"sub": owner_id})
    monkeypatch.setattr("app.main.crud_client.get_user", fake_get_user)
    monkeypatch.setattr("app.api.files.file_storage.upload", fake_upload)
    monkeypatch.setattr("app.api.files.file_storage.delete", fake_delete)
    monkeypatch.setattr(
        "app.api.files.file_storage.create_download_url", fake_download_url
    )
    monkeypatch.setattr("app.api.files.crud_client.create_library_file", fake_create)
    monkeypatch.setattr("app.api.files.crud_client.list_library_files", fake_list)
    monkeypatch.setattr("app.api.files.crud_client.get_library_file", fake_get)
    monkeypatch.setattr(
        "app.api.files.crud_client.delete_library_file", fake_delete_metadata
    )

    return TestClient(app), owner_id, records, uploaded


def test_upload_list_download_and_delete_pdf(file_api):
    client, owner_id, records, uploaded = file_api
    headers = {"Authorization": "Bearer test-token"}

    uploaded_response = client.post(
        "/api/files",
        headers=headers,
        files={"file": ("Quarterly Review.pdf", b"%PDF-1.4\ncontent", "application/pdf")},
    )
    assert uploaded_response.status_code == 201
    body = uploaded_response.json()
    assert body["original_name"] == "Quarterly Review.pdf"
    assert body["upload_status"] == "ready"
    file_id = body["file_id"]
    object_key = records[file_id]["object_key"]
    assert object_key.startswith(f"presentations/{owner_id}/{file_id}/")
    assert uploaded[object_key].startswith(b"%PDF-")

    listed = client.get("/api/files", headers=headers)
    assert listed.status_code == 200
    assert [item["file_id"] for item in listed.json()] == [file_id]

    download = client.get(f"/api/files/{file_id}/download", headers=headers)
    assert download.status_code == 200
    assert download.json()["url"].startswith("https://signed.example/")

    deleted = client.delete(f"/api/files/{file_id}", headers=headers)
    assert deleted.status_code == 204
    assert file_id not in records
    assert object_key not in uploaded


def test_uploads_valid_pptx(file_api):
    client, _, _, _ = file_api
    pptx = io.BytesIO()
    with zipfile.ZipFile(pptx, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types />")
        archive.writestr("ppt/presentation.xml", "<p:presentation />")

    response = client.post(
        "/api/files",
        headers={"Authorization": "Bearer test-token"},
        files={
            "file": (
                "deck.pptx",
                pptx.getvalue(),
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            )
        },
    )
    assert response.status_code == 201
    assert response.json()["content_type"].endswith("presentationml.presentation")


def test_rejects_oversized_file(file_api, monkeypatch):
    client, _, _, _ = file_api
    monkeypatch.setattr("app.api.files.MAX_FILE_SIZE", 8)
    response = client.post(
        "/api/files",
        headers={"Authorization": "Bearer test-token"},
        files={"file": ("large.pdf", b"%PDF-1234", "application/pdf")},
    )
    assert response.status_code == 413


@pytest.mark.parametrize(
    ("filename", "content", "content_type", "expected_status"),
    [
        ("notes.txt", b"hello", "text/plain", 400),
        ("fake.pdf", b"not a pdf", "application/pdf", 400),
        ("slides.pptx", b"not a zip", "application/vnd.openxmlformats-officedocument.presentationml.presentation", 400),
    ],
)
def test_rejects_invalid_presentations(
    file_api, filename, content, content_type, expected_status
):
    client, _, _, _ = file_api
    response = client.post(
        "/api/files",
        headers={"Authorization": "Bearer test-token"},
        files={"file": (filename, content, content_type)},
    )
    assert response.status_code == expected_status


def test_blocks_other_users_from_download_and_delete(file_api, monkeypatch):
    client, owner_id, records, uploaded = file_api
    file_id = str(uuid.uuid4())
    object_key = f"presentations/{owner_id}/{file_id}/private.pdf"
    records[file_id] = {
        "file_id": file_id,
        "user_id": owner_id,
        "original_name": "private.pdf",
        "object_key": object_key,
        "content_type": "application/pdf",
        "size_bytes": 12,
        "upload_status": "ready",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    uploaded[object_key] = b"%PDF-private"
    other_id = str(uuid.uuid4())
    monkeypatch.setattr("app.main.verify_token", lambda token: {"sub": other_id})
    headers = {"Authorization": "Bearer other-user"}

    assert client.get(f"/api/files/{file_id}/download", headers=headers).status_code == 403
    assert client.delete(f"/api/files/{file_id}", headers=headers).status_code == 403
    assert object_key in uploaded


def test_removes_r2_object_when_metadata_save_fails(file_api, monkeypatch):
    client, _, _, uploaded = file_api

    async def fail_create(_payload: dict):
        request = httpx.Request("POST", "http://crud/files")
        raise httpx.RequestError("CRUD unavailable", request=request)

    monkeypatch.setattr("app.api.files.crud_client.create_library_file", fail_create)
    response = client.post(
        "/api/files",
        headers={"Authorization": "Bearer test-token"},
        files={"file": ("cleanup.pdf", b"%PDF-1.4\ncontent", "application/pdf")},
    )
    assert response.status_code == 502
    assert uploaded == {}
