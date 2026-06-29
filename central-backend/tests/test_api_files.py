import io
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pymupdf
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import presentation_processing as processing_service


@pytest.fixture
def file_api(monkeypatch):
    owner_id = str(uuid.uuid4())
    records: dict[str, dict] = {}
    uploaded: dict[str, bytes] = {}
    slides: dict[str, list[dict]] = {}

    async def fake_get_user(user_id: str):
        return {"user_id": user_id, "role": "user", "is_active": True}

    async def fake_upload(file_object, object_key: str, content_type: str):
        uploaded[object_key] = file_object.read()

    async def fake_delete(object_key: str):
        uploaded.pop(object_key, None)

    async def fake_delete_many(object_keys: list[str]):
        for object_key in object_keys:
            uploaded.pop(object_key, None)

    async def fake_download_url(object_key: str):
        return f"https://signed.example/{object_key}?expires=300"

    async def fake_create(payload: dict):
        record = {
            **payload,
            "processing_status": payload.get("processing_status", "queued"),
            "slide_count": None,
            "processing_error": None,
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
        slides.pop(file_id, None)

    async def fake_update_processing(file_id: str, payload: dict):
        records[file_id].update(payload)
        return records[file_id]

    async def fake_get_slides(file_id: str):
        return slides.get(file_id, [])

    async def fake_process(file_id: str):
        records[file_id]["processing_status"] = "ready"
        records[file_id]["slide_count"] = len(slides.get(file_id, []))

    monkeypatch.setattr("app.main.verify_token", lambda token: {"sub": owner_id})
    monkeypatch.setattr("app.main.crud_client.get_user", fake_get_user)
    monkeypatch.setattr("app.api.files.file_storage.upload", fake_upload)
    monkeypatch.setattr("app.api.files.file_storage.delete", fake_delete)
    monkeypatch.setattr("app.api.files.file_storage.delete_many", fake_delete_many)
    monkeypatch.setattr(
        "app.api.files.file_storage.create_download_url", fake_download_url
    )
    monkeypatch.setattr("app.api.files.crud_client.create_library_file", fake_create)
    monkeypatch.setattr("app.api.files.crud_client.list_library_files", fake_list)
    monkeypatch.setattr("app.api.files.crud_client.get_library_file", fake_get)
    monkeypatch.setattr(
        "app.api.files.crud_client.delete_library_file", fake_delete_metadata
    )
    monkeypatch.setattr(
        "app.api.files.crud_client.update_library_file_processing",
        fake_update_processing,
    )
    monkeypatch.setattr(
        "app.api.files.crud_client.get_presentation_slides", fake_get_slides
    )
    monkeypatch.setattr("app.api.files.process_presentation", fake_process)

    return TestClient(app), owner_id, records, uploaded, slides


def test_upload_list_download_and_delete_pdf(file_api):
    client, owner_id, records, uploaded, slides = file_api
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
    assert body["processing_status"] == "queued"
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
    client, _, _, _, _ = file_api
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
    client, _, _, _, _ = file_api
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
    client, _, _, _, _ = file_api
    response = client.post(
        "/api/files",
        headers={"Authorization": "Bearer test-token"},
        files={"file": (filename, content, content_type)},
    )
    assert response.status_code == expected_status


def test_blocks_other_users_from_download_and_delete(file_api, monkeypatch):
    client, owner_id, records, uploaded, _slides = file_api
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
        "processing_status": "ready",
        "slide_count": 0,
        "processing_error": None,
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
    client, _, _, uploaded, _slides = file_api

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


def test_slide_manifest_is_created_only_on_selection(file_api):
    client, owner_id, records, _, slides = file_api
    file_id = str(uuid.uuid4())
    records[file_id] = {
        "file_id": file_id,
        "user_id": owner_id,
        "original_name": "ready.pdf",
        "object_key": f"presentations/{owner_id}/{file_id}/ready.pdf",
        "content_type": "application/pdf",
        "size_bytes": 100,
        "upload_status": "ready",
        "processing_status": "ready",
        "slide_count": 2,
        "processing_error": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    slides[file_id] = [
        {
            "slide_number": number,
            "object_key": f"presentations/{owner_id}/{file_id}/slides/{number:04d}.png",
            "width": 1920,
            "height": 1080,
            "size_bytes": 1000,
        }
        for number in (1, 2)
    ]
    response = client.get(
        f"/api/files/{file_id}/slides",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["slide_count"] == 2
    assert [slide["number"] for slide in body["slides"]] == [1, 2]
    assert all(slide["url"].startswith("https://signed.example/") for slide in body["slides"])


def test_deletes_stale_queued_metadata_when_r2_object_is_already_missing(file_api):
    client, owner_id, records, uploaded, _slides = file_api
    file_id = str(uuid.uuid4())
    records[file_id] = {
        "file_id": file_id,
        "user_id": owner_id,
        "original_name": "manually-removed.pdf",
        "object_key": f"presentations/{owner_id}/{file_id}/manually-removed.pdf",
        "content_type": "application/pdf",
        "size_bytes": 100,
        "upload_status": "ready",
        "processing_status": "queued",
        "slide_count": None,
        "processing_error": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    assert uploaded == {}

    response = client.delete(
        f"/api/files/{file_id}",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 204
    assert file_id not in records


@pytest.mark.asyncio
async def test_pdf_processing_uploads_ordered_pngs(monkeypatch):
    file_id = str(uuid.uuid4())
    record = {
        "file_id": file_id,
        "object_key": f"presentations/user/{file_id}/deck.pdf",
        "content_type": "application/pdf",
    }
    uploaded: dict[str, bytes] = {}
    processing_updates: list[dict] = []
    saved_slides: list[dict] = []

    async def fake_get(_file_id: str):
        return record

    async def fake_update(_file_id: str, payload: dict):
        processing_updates.append(payload)
        return {**record, **payload}

    async def fake_download(_object_key: str, local_path: Path):
        document = pymupdf.open()
        document.new_page(width=1280, height=720).insert_text((72, 72), "Slide one")
        document.new_page(width=1280, height=720).insert_text((72, 72), "Slide two")
        document.save(local_path)
        document.close()

    async def fake_upload(local_path: Path, object_key: str, _content_type: str):
        uploaded[object_key] = local_path.read_bytes()

    async def fake_replace(_file_id: str, slides: list[dict]):
        saved_slides.extend(slides)
        return slides

    monkeypatch.setattr(processing_service.crud_client, "get_library_file", fake_get)
    monkeypatch.setattr(
        processing_service.crud_client, "update_library_file_processing", fake_update
    )
    monkeypatch.setattr(
        processing_service.crud_client, "replace_presentation_slides", fake_replace
    )
    monkeypatch.setattr(processing_service.file_storage, "download_to_path", fake_download)
    monkeypatch.setattr(processing_service.file_storage, "upload_path", fake_upload)

    await processing_service.process_presentation(file_id)

    assert processing_updates[0]["processing_status"] == "processing"
    assert [slide["slide_number"] for slide in saved_slides] == [1, 2]
    assert list(uploaded) == [
        f"presentations/user/{file_id}/slides/0001.png",
        f"presentations/user/{file_id}/slides/0002.png",
    ]
    assert all(slide["width"] == 1920 for slide in saved_slides)


@pytest.mark.asyncio
async def test_pptx_processing_converts_to_pdf_before_rendering(monkeypatch):
    file_id = str(uuid.uuid4())
    record = {
        "file_id": file_id,
        "object_key": f"presentations/user/{file_id}/deck.pptx",
        "content_type": (
            "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        ),
    }
    converter_called = False
    saved_slides: list[dict] = []

    async def fake_get(_file_id: str):
        return record

    async def fake_update(_file_id: str, payload: dict):
        return {**record, **payload}

    async def fake_download(_object_key: str, local_path: Path):
        local_path.write_bytes(b"pptx source")

    async def fake_convert(source_path: Path, pdf_path: Path):
        nonlocal converter_called
        converter_called = True
        assert source_path.suffix == ".pptx"
        document = pymupdf.open()
        document.new_page(width=1280, height=720).insert_text((72, 72), "Converted")
        document.save(pdf_path)
        document.close()

    async def fake_upload(_local_path: Path, _object_key: str, _content_type: str):
        return None

    async def fake_replace(_file_id: str, slides: list[dict]):
        saved_slides.extend(slides)
        return slides

    monkeypatch.setattr(processing_service.crud_client, "get_library_file", fake_get)
    monkeypatch.setattr(
        processing_service.crud_client, "update_library_file_processing", fake_update
    )
    monkeypatch.setattr(
        processing_service.crud_client, "replace_presentation_slides", fake_replace
    )
    monkeypatch.setattr(processing_service.file_storage, "download_to_path", fake_download)
    monkeypatch.setattr(processing_service.file_storage, "upload_path", fake_upload)
    monkeypatch.setattr(processing_service, "_convert_pptx_to_pdf", fake_convert)

    await processing_service.process_presentation(file_id)

    assert converter_called is True
    assert [slide["slide_number"] for slide in saved_slides] == [1]


@pytest.mark.asyncio
async def test_processing_failure_removes_partially_uploaded_slides(monkeypatch):
    file_id = str(uuid.uuid4())
    prefix = f"presentations/user/{file_id}"
    record = {
        "file_id": file_id,
        "object_key": f"{prefix}/deck.pdf",
        "content_type": "application/pdf",
    }
    uploaded_keys: list[str] = []
    deleted_keys: list[str] = []
    updates: list[dict] = []

    async def fake_get(_file_id: str):
        return record

    async def fake_update(_file_id: str, payload: dict):
        updates.append(payload)
        return {**record, **payload}

    async def fake_download(_object_key: str, local_path: Path):
        document = pymupdf.open()
        document.new_page()
        document.new_page()
        document.save(local_path)
        document.close()

    async def fake_upload(_local_path: Path, object_key: str, _content_type: str):
        if object_key.endswith("0002.png"):
            raise RuntimeError("R2 upload failed")
        uploaded_keys.append(object_key)

    async def fake_delete(object_key: str):
        deleted_keys.append(object_key)

    monkeypatch.setattr(processing_service.crud_client, "get_library_file", fake_get)
    monkeypatch.setattr(
        processing_service.crud_client, "update_library_file_processing", fake_update
    )
    monkeypatch.setattr(processing_service.file_storage, "download_to_path", fake_download)
    monkeypatch.setattr(processing_service.file_storage, "upload_path", fake_upload)
    monkeypatch.setattr(processing_service.file_storage, "delete", fake_delete)

    await processing_service.process_presentation(file_id)

    assert uploaded_keys == [f"{prefix}/slides/0001.png"]
    assert deleted_keys == uploaded_keys
    assert updates[-1]["processing_status"] == "failed"
    assert updates[-1]["processing_error"] == "Presentation processing failed"
