from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class LibraryFileResponse(BaseModel):
    file_id: str
    original_name: str
    content_type: str
    size_bytes: int
    upload_status: Literal["ready"]
    processing_status: Literal["queued", "processing", "ready", "failed"]
    slide_count: int | None = None
    processing_error: str | None = None
    created_at: datetime


class FileDownloadResponse(BaseModel):
    url: str
    expires_at: datetime


class PresentationSlideResponse(BaseModel):
    number: int
    width: int
    height: int
    size_bytes: int
    url: str
    expires_at: datetime


class PresentationSlidesManifest(BaseModel):
    file_id: str
    original_name: str
    processing_status: Literal["ready"]
    slide_count: int
    slides: list[PresentationSlideResponse]
