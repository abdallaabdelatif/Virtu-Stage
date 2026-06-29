import io
import uuid

from botocore.exceptions import ClientError
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


def _image_bytes(format_name: str = "PNG") -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (800, 400), (92, 124, 255)).save(output, format=format_name)
    return output.getvalue()


def _avatar_client(monkeypatch, old_key: str | None = None):
    user_id = str(uuid.uuid4())
    objects: dict[str, bytes] = {}
    deleted: list[str] = []
    updated: list[str] = []

    async def fake_get_user(requested_user_id: str):
        return {
            "user_id": requested_user_id,
            "role": "user",
            "is_active": True,
            "avatar_key": old_key,
        }

    async def fake_upload(file_object, object_key: str):
        objects[object_key] = file_object.read()

    async def fake_delete(object_key: str):
        deleted.append(object_key)
        objects.pop(object_key, None)

    async def fake_update(_user_id: str, object_key: str):
        updated.append(object_key)
        return {"avatar_key": object_key}

    async def fake_read(object_key: str):
        if object_key not in objects:
            raise ClientError(
                {"Error": {"Code": "NoSuchKey", "Message": "missing"}},
                "GetObject",
            )
        return objects[object_key]

    monkeypatch.setattr("app.main.verify_token", lambda _token: {"sub": user_id})
    monkeypatch.setattr("app.main.crud_client.get_user", fake_get_user)
    monkeypatch.setattr("app.api.avatars.file_storage.upload_avatar", fake_upload)
    monkeypatch.setattr("app.api.avatars.file_storage.delete_avatar", fake_delete)
    monkeypatch.setattr("app.api.avatars.file_storage.read_avatar", fake_read)
    monkeypatch.setattr("app.api.avatars.crud_client.update_user_avatar", fake_update)
    return TestClient(app), user_id, objects, deleted, updated


def test_upload_normalizes_avatar_and_replaces_old_object(monkeypatch):
    old_key = f"avatars/{uuid.uuid4()}/{uuid.uuid4()}.webp"
    client, user_id, objects, deleted, updated = _avatar_client(monkeypatch, old_key)

    response = client.post(
        "/api/users/me/avatar",
        headers={"Authorization": "Bearer test-token"},
        files={"file": ("avatar.png", _image_bytes(), "image/png")},
    )

    assert response.status_code == 201
    assert response.json()["avatar_url"].endswith(f"/{updated[0].split('/')[-1]}")
    assert updated[0].startswith(f"avatars/{user_id}/")
    assert old_key in deleted
    with Image.open(io.BytesIO(objects[updated[0]])) as image:
        assert image.format == "WEBP"
        assert image.size == (512, 512)


def test_upload_rejects_spoofed_image(monkeypatch):
    client, _, objects, _, updated = _avatar_client(monkeypatch)
    response = client.post(
        "/api/users/me/avatar",
        headers={"Authorization": "Bearer test-token"},
        files={"file": ("avatar.png", b"not-an-image", "image/png")},
    )

    assert response.status_code == 422
    assert objects == {}
    assert updated == []


def test_public_avatar_read_is_cacheable(monkeypatch):
    client, user_id, objects, _, _ = _avatar_client(monkeypatch)
    avatar_id = str(uuid.uuid4())
    object_key = f"avatars/{user_id}/{avatar_id}.webp"
    objects[object_key] = _image_bytes("WEBP")

    response = client.get(f"/api/avatars/{user_id}/{avatar_id}.webp")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/webp"
    assert "immutable" in response.headers["cache-control"]


def test_missing_public_avatar_returns_404(monkeypatch):
    client, user_id, _, _, _ = _avatar_client(monkeypatch)
    response = client.get(f"/api/avatars/{user_id}/{uuid.uuid4()}.webp")
    assert response.status_code == 404
