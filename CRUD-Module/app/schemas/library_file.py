import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LibraryFileCreate(BaseModel):
    file_id: uuid.UUID
    user_id: uuid.UUID
    original_name: str = Field(min_length=1, max_length=255)
    object_key: str = Field(min_length=1, max_length=1024)
    content_type: Literal[
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ]
    size_bytes: int = Field(gt=0, le=50 * 1024 * 1024)
    upload_status: Literal["ready"] = "ready"


class LibraryFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    file_id: uuid.UUID
    user_id: uuid.UUID
    original_name: str
    object_key: str
    content_type: str
    size_bytes: int
    upload_status: str
    created_at: datetime
    updated_at: datetime
