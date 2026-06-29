from __future__ import annotations

import io
import logging
import uuid

import httpx
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from app.auth.deps import get_current_active_user
from app.auth.routes import _http_error_detail
from app.clients.crud_client import crud_client
from app.config import AVATAR_MAX_BYTES
from app.services.avatars import InvalidAvatarError, avatar_url_from_key, normalize_avatar
from app.services.file_storage import StorageConfigurationError, file_storage


router = APIRouter(tags=["avatars"])
logger = logging.getLogger(__name__)
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


class AvatarUploadResponse(BaseModel):
    avatar_url: str


async def _delete_avatar_best_effort(object_key: str | None) -> None:
    if not object_key or not object_key.startswith("avatars/"):
        return
    try:
        await file_storage.delete_avatar(object_key)
    except Exception:
        logger.exception("Unable to clean up avatar object %s", object_key)


@router.post(
    "/api/users/me/avatar",
    response_model=AvatarUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_avatar(
    file: UploadFile = File(...),
    user=Depends(get_current_active_user),
) -> AvatarUploadResponse:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Avatar must be a JPEG, PNG, or WebP image",
        )

    raw = await file.read(AVATAR_MAX_BYTES + 1)
    await file.close()
    if len(raw) > AVATAR_MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Avatar must be {AVATAR_MAX_BYTES // (1024 * 1024)}MB or smaller",
        )
    if not raw:
        raise HTTPException(status_code=422, detail="Avatar file is empty")

    try:
        normalized = await run_in_threadpool(normalize_avatar, raw)
    except InvalidAvatarError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    user_id = str(user["user_id"])
    avatar_id = str(uuid.uuid4())
    object_key = f"avatars/{user_id}/{avatar_id}.webp"
    old_key = user.get("avatar_key")

    try:
        await file_storage.upload_avatar(io.BytesIO(normalized), object_key)
    except StorageConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(status_code=502, detail="Avatar storage is unavailable") from exc

    try:
        await crud_client.update_user_avatar(user_id, object_key)
    except httpx.HTTPStatusError as exc:
        await _delete_avatar_best_effort(object_key)
        if exc.response.status_code in (403, 404, 422):
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=_http_error_detail(exc, "Unable to update avatar"),
            ) from exc
        raise HTTPException(status_code=502, detail="CRUD service is unavailable") from exc
    except httpx.HTTPError as exc:
        await _delete_avatar_best_effort(object_key)
        raise HTTPException(status_code=502, detail="CRUD service is unavailable") from exc

    await _delete_avatar_best_effort(old_key)
    avatar_url = avatar_url_from_key(object_key)
    if not avatar_url:
        await _delete_avatar_best_effort(object_key)
        raise HTTPException(status_code=500, detail="Unable to create avatar URL")
    return AvatarUploadResponse(avatar_url=avatar_url)


@router.get("/api/avatars/{user_id}/{avatar_id}.webp")
async def get_avatar(user_id: uuid.UUID, avatar_id: uuid.UUID) -> Response:
    object_key = f"avatars/{user_id}/{avatar_id}.webp"
    try:
        content = await file_storage.read_avatar(object_key)
    except ClientError as exc:
        error_code = str(exc.response.get("Error", {}).get("Code", ""))
        if error_code in {"NoSuchKey", "404", "NotFound"}:
            raise HTTPException(status_code=404, detail="Avatar not found") from exc
        raise HTTPException(status_code=502, detail="Avatar storage is unavailable") from exc
    except StorageConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except BotoCoreError as exc:
        raise HTTPException(status_code=502, detail="Avatar storage is unavailable") from exc

    return Response(
        content=content,
        media_type="image/webp",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )
