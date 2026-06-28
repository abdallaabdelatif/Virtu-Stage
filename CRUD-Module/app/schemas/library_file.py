import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ProcessingStatus = Literal["queued", "processing", "ready", "failed"]


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
    processing_status: ProcessingStatus = "queued"


class LibraryFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    file_id: uuid.UUID
    user_id: uuid.UUID
    original_name: str
    object_key: str
    content_type: str
    size_bytes: int
    upload_status: str
    processing_status: ProcessingStatus
    slide_count: int | None = None
    processing_error: str | None = None
    processed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class LibraryFileProcessingUpdate(BaseModel):
    processing_status: ProcessingStatus
    slide_count: int | None = Field(default=None, ge=0, le=100)
    processing_error: str | None = Field(default=None, max_length=1000)
    processed_at: datetime | None = None


class PresentationSlideCreate(BaseModel):
    slide_number: int = Field(ge=1, le=100)
    object_key: str = Field(min_length=1, max_length=1024)
    width: int = Field(gt=0, le=8192)
    height: int = Field(gt=0, le=8192)
    size_bytes: int = Field(gt=0)


class PresentationSlidesReplace(BaseModel):
    slides: list[PresentationSlideCreate] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_order(self) -> "PresentationSlidesReplace":
        numbers = [slide.slide_number for slide in self.slides]
        if numbers != list(range(1, len(numbers) + 1)):
            raise ValueError("Slides must be ordered consecutively starting at 1")
        return self


class PresentationSlideResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slide_id: uuid.UUID
    file_id: uuid.UUID
    slide_number: int
    object_key: str
    width: int
    height: int
    size_bytes: int
    created_at: datetime
