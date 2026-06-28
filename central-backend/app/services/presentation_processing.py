from __future__ import annotations

import asyncio
import tempfile
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

import httpx
import pymupdf
from starlette.concurrency import run_in_threadpool

from app.clients.crud_client import crud_client
from app.config import (
    GOTENBERG_TIMEOUT_SECONDS,
    GOTENBERG_URL,
    PRESENTATION_IMAGE_WIDTH,
    PRESENTATION_MAX_SLIDES,
)
from app.services.file_storage import file_storage


class PresentationProcessingError(RuntimeError):
    pass


_presentation_locks: dict[str, asyncio.Lock] = {}


@asynccontextmanager
async def presentation_operation(file_id: str) -> AsyncIterator[None]:
    """Serialize conversion and deletion for one presentation in this process."""
    lock = _presentation_locks.setdefault(file_id, asyncio.Lock())
    async with lock:
        yield


@dataclass(frozen=True)
class RenderedSlide:
    number: int
    path: Path
    width: int
    height: int
    size_bytes: int


async def _convert_pptx_to_pdf(source_path: Path, pdf_path: Path) -> None:
    try:
        with source_path.open("rb") as source:
            async with httpx.AsyncClient(timeout=GOTENBERG_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    f"{GOTENBERG_URL}/forms/libreoffice/convert",
                    files={
                        "files": (
                            source_path.name,
                            source,
                            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        )
                    },
                )
        response.raise_for_status()
    except (httpx.TimeoutException, httpx.NetworkError) as exc:
        raise PresentationProcessingError(
            "Presentation converter is unavailable"
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise PresentationProcessingError(
            "PowerPoint conversion was rejected"
        ) from exc
    await run_in_threadpool(pdf_path.write_bytes, response.content)


def _render_pdf(pdf_path: Path, output_directory: Path) -> list[RenderedSlide]:
    try:
        document = pymupdf.open(pdf_path)
    except Exception as exc:
        raise PresentationProcessingError("The generated PDF could not be opened") from exc

    with document:
        if document.page_count == 0:
            raise PresentationProcessingError("The presentation contains no pages")
        if document.page_count > PRESENTATION_MAX_SLIDES:
            raise PresentationProcessingError(
                f"Presentation exceeds the {PRESENTATION_MAX_SLIDES}-slide limit"
            )

        slides: list[RenderedSlide] = []
        for number, page in enumerate(document, start=1):
            scale = PRESENTATION_IMAGE_WIDTH / page.rect.width
            pixmap = page.get_pixmap(
                matrix=pymupdf.Matrix(scale, scale),
                alpha=False,
            )
            path = output_directory / f"{number:04d}.png"
            pixmap.save(path)
            slides.append(
                RenderedSlide(
                    number=number,
                    path=path,
                    width=pixmap.width,
                    height=pixmap.height,
                    size_bytes=path.stat().st_size,
                )
            )
        return slides


def _safe_processing_error(exc: Exception) -> str:
    if isinstance(exc, PresentationProcessingError):
        return str(exc)
    return "Presentation processing failed"


async def _process_presentation(file_id: str) -> None:
    uploaded_slide_keys: list[str] = []
    try:
        record = await crud_client.get_library_file(file_id)
        if record is None:
            return
        await crud_client.update_library_file_processing(
            file_id,
            {
                "processing_status": "processing",
                "slide_count": None,
                "processing_error": None,
                "processed_at": None,
            },
        )

        suffix = ".pptx" if record["content_type"].endswith("presentation") else ".pdf"
        prefix = record["object_key"].rsplit("/", 1)[0]
        with tempfile.TemporaryDirectory(prefix="virtustage-presentation-") as temporary:
            temporary_directory = Path(temporary)
            source_path = temporary_directory / f"source{suffix}"
            pdf_path = temporary_directory / "presentation.pdf"
            slides_directory = temporary_directory / "slides"
            slides_directory.mkdir()

            await file_storage.download_to_path(record["object_key"], source_path)
            if suffix == ".pptx":
                await _convert_pptx_to_pdf(source_path, pdf_path)
            else:
                pdf_path = source_path

            rendered_slides = await run_in_threadpool(
                _render_pdf, pdf_path, slides_directory
            )
            slide_metadata: list[dict] = []
            for slide in rendered_slides:
                object_key = f"{prefix}/slides/{slide.number:04d}.png"
                await file_storage.upload_path(slide.path, object_key, "image/png")
                uploaded_slide_keys.append(object_key)
                slide_metadata.append(
                    {
                        "slide_number": slide.number,
                        "object_key": object_key,
                        "width": slide.width,
                        "height": slide.height,
                        "size_bytes": slide.size_bytes,
                    }
                )
            await crud_client.replace_presentation_slides(file_id, slide_metadata)
    except Exception as exc:
        for object_key in uploaded_slide_keys:
            try:
                await file_storage.delete(object_key)
            except Exception:
                pass
        try:
            await crud_client.update_library_file_processing(
                file_id,
                {
                    "processing_status": "failed",
                    "slide_count": None,
                    "processing_error": _safe_processing_error(exc),
                    "processed_at": None,
                },
            )
        except Exception:
            pass


async def process_presentation(file_id: str) -> None:
    async with presentation_operation(file_id):
        await _process_presentation(file_id)
