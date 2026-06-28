from __future__ import annotations

import re
import uuid
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from app.api.schemas.files import FileDownloadResponse, LibraryFileResponse
from app.auth.deps import get_current_active_user
from app.clients.crud_client import crud_client
from app.config import R2_SIGNED_URL_EXPIRES_SECONDS
from app.services.file_storage import StorageConfigurationError, file_storage

router = APIRouter(prefix="/api/files", tags=["files"])

MAX_FILE_SIZE = 50 * 1024 * 1024
MAX_PPTX_UNCOMPRESSED_SIZE = 250 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
    ".pdf": {"application/pdf"},
    ".pptx": {
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    },
}
CANONICAL_CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".pptx": (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    ),
}


def _safe_filename(filename: str) -> str:
    name = Path(filename.replace("\\", "/")).name
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(name).stem).strip("._")
    extension = Path(name).suffix.lower()
    return f"{(stem or 'presentation')[:200]}{extension}"


def _validate_pptx_archive(file_object) -> None:
    try:
        with zipfile.ZipFile(file_object) as archive:
            names = set(archive.namelist())
            if "[Content_Types].xml" not in names or "ppt/presentation.xml" not in names:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The selected file is not a valid PPTX presentation",
                )
            uncompressed_size = sum(item.file_size for item in archive.infolist())
            if uncompressed_size > MAX_PPTX_UNCOMPRESSED_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="The PPTX expands beyond the allowed size",
                )
    except zipfile.BadZipFile as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The selected file is not a valid PPTX presentation",
        ) from exc
    finally:
        file_object.seek(0)


async def _validate_upload(file: UploadFile) -> tuple[str, str, int]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="A filename is required")
    if len(file.filename) > 255:
        raise HTTPException(status_code=400, detail="Filename is too long")

    safe_name = _safe_filename(file.filename)
    extension = Path(safe_name).suffix.lower()
    if extension not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and PPTX presentations are supported",
        )
    if file.content_type not in ALLOWED_CONTENT_TYPES[extension]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Content type does not match {extension[1:].upper()}",
        )

    await run_in_threadpool(file.file.seek, 0, 2)
    size_bytes = await run_in_threadpool(file.file.tell)
    await file.seek(0)
    if size_bytes <= 0:
        raise HTTPException(status_code=400, detail="The selected file is empty")
    if size_bytes > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large (maximum 50 MB)",
        )

    signature = await file.read(8)
    await file.seek(0)
    if extension == ".pdf" and not signature.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="The selected file is not a valid PDF")
    if extension == ".pptx":
        await run_in_threadpool(_validate_pptx_archive, file.file)

    return safe_name, CANONICAL_CONTENT_TYPES[extension], size_bytes


def _public_file(record: dict) -> dict:
    return {
        "file_id": str(record["file_id"]),
        "original_name": record["original_name"],
        "content_type": record["content_type"],
        "size_bytes": record["size_bytes"],
        "upload_status": record["upload_status"],
        "created_at": record["created_at"],
    }


async def _get_owned_file(file_id: str, user: dict) -> dict:
    try:
        record = await crud_client.get_library_file(file_id)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="CRUD service is unavailable") from exc
    if record is None:
        raise HTTPException(status_code=404, detail="File not found")
    if str(record["user_id"]) != str(user["user_id"]):
        raise HTTPException(status_code=403, detail="You do not have access to this file")
    return record


@router.get("", response_model=list[LibraryFileResponse])
async def list_files(user=Depends(get_current_active_user)):
    try:
        records = await crud_client.list_library_files(str(user["user_id"]))
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="CRUD service is unavailable") from exc
    return [_public_file(record) for record in records]


@router.post("", response_model=LibraryFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...), user=Depends(get_current_active_user)
):
    safe_name, content_type, size_bytes = await _validate_upload(file)
    file_id = str(uuid.uuid4())
    object_key = f"presentations/{user['user_id']}/{file_id}/{safe_name}"

    try:
        await file.seek(0)
        await file_storage.upload(file.file, object_key, content_type)
        try:
            record = await crud_client.create_library_file(
                {
                    "file_id": file_id,
                    "user_id": str(user["user_id"]),
                    "original_name": file.filename,
                    "object_key": object_key,
                    "content_type": content_type,
                    "size_bytes": size_bytes,
                    "upload_status": "ready",
                }
            )
        except httpx.HTTPError:
            await file_storage.delete(object_key)
            raise
    except StorageConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(status_code=502, detail="File storage is unavailable") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Could not save file metadata") from exc
    finally:
        await file.close()

    return _public_file(record)


@router.get("/{file_id}/download", response_model=FileDownloadResponse)
async def download_file(file_id: uuid.UUID, user=Depends(get_current_active_user)):
    record = await _get_owned_file(str(file_id), user)
    try:
        url = await file_storage.create_download_url(record["object_key"])
    except StorageConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(status_code=502, detail="File storage is unavailable") from exc
    return {
        "url": url,
        "expires_at": datetime.now(timezone.utc)
        + timedelta(seconds=R2_SIGNED_URL_EXPIRES_SECONDS),
    }


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(file_id: uuid.UUID, user=Depends(get_current_active_user)):
    record = await _get_owned_file(str(file_id), user)
    try:
        await file_storage.delete(record["object_key"])
        await crud_client.delete_library_file(str(file_id))
    except StorageConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(status_code=502, detail="File storage is unavailable") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Could not delete file metadata") from exc
