import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies.internal import require_internal_api_key
from app.models.library_file import LibraryFile
from app.models.presentation_slide import PresentationSlide
from app.schemas.library_file import (
    LibraryFileCreate,
    LibraryFileProcessingUpdate,
    LibraryFileResponse,
    PresentationSlideResponse,
    PresentationSlidesReplace,
)

router = APIRouter(prefix="/files", tags=["library-files"])


@router.post("", response_model=LibraryFileResponse, status_code=status.HTTP_201_CREATED)
async def create_file(
    payload: LibraryFileCreate,
    db: AsyncSession = Depends(get_session),
    _internal_access: None = Depends(require_internal_api_key),
) -> LibraryFile:
    library_file = LibraryFile(**payload.model_dump())
    db.add(library_file)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="File metadata already exists or references an invalid user",
        ) from exc
    await db.refresh(library_file)
    return library_file


@router.get("/user/{user_id}", response_model=list[LibraryFileResponse])
async def list_files_by_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    _internal_access: None = Depends(require_internal_api_key),
) -> list[LibraryFile]:
    result = await db.execute(
        select(LibraryFile)
        .where(LibraryFile.user_id == user_id)
        .order_by(LibraryFile.created_at.desc())
    )
    return list(result.scalars().all())


@router.patch("/{file_id}/processing", response_model=LibraryFileResponse)
async def update_processing_status(
    file_id: uuid.UUID,
    payload: LibraryFileProcessingUpdate,
    db: AsyncSession = Depends(get_session),
    _internal_access: None = Depends(require_internal_api_key),
) -> LibraryFile:
    library_file = await db.get(LibraryFile, file_id)
    if not library_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    for field, value in payload.model_dump().items():
        setattr(library_file, field, value)
    await db.commit()
    await db.refresh(library_file)
    return library_file


@router.get("/{file_id}/slides", response_model=list[PresentationSlideResponse])
async def list_file_slides(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    _internal_access: None = Depends(require_internal_api_key),
) -> list[PresentationSlide]:
    if not await db.get(LibraryFile, file_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    result = await db.execute(
        select(PresentationSlide)
        .where(PresentationSlide.file_id == file_id)
        .order_by(PresentationSlide.slide_number)
    )
    return list(result.scalars().all())


@router.put("/{file_id}/slides", response_model=list[PresentationSlideResponse])
async def replace_file_slides(
    file_id: uuid.UUID,
    payload: PresentationSlidesReplace,
    db: AsyncSession = Depends(get_session),
    _internal_access: None = Depends(require_internal_api_key),
) -> list[PresentationSlide]:
    library_file = await db.get(LibraryFile, file_id)
    if not library_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    await db.execute(delete(PresentationSlide).where(PresentationSlide.file_id == file_id))
    slides = [
        PresentationSlide(file_id=file_id, **slide.model_dump())
        for slide in payload.slides
    ]
    db.add_all(slides)
    library_file.processing_status = "ready"
    library_file.processing_error = None
    library_file.slide_count = len(slides)
    library_file.processed_at = datetime.now(timezone.utc)
    await db.commit()
    for slide in slides:
        await db.refresh(slide)
    return slides


@router.get("/{file_id}", response_model=LibraryFileResponse)
async def get_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    _internal_access: None = Depends(require_internal_api_key),
) -> LibraryFile:
    library_file = await db.get(LibraryFile, file_id)
    if not library_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return library_file


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    _internal_access: None = Depends(require_internal_api_key),
) -> Response:
    library_file = await db.get(LibraryFile, file_id)
    if not library_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    await db.delete(library_file)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
