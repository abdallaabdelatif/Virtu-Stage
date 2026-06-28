from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class LibraryFileResponse(BaseModel):
    file_id: str
    original_name: str
    content_type: str
    size_bytes: int
    upload_status: Literal["ready"]
    created_at: datetime


class FileDownloadResponse(BaseModel):
    url: str
    expires_at: datetime
