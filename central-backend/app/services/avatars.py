from __future__ import annotations

import io
import re

from PIL import Image, ImageOps, UnidentifiedImageError

from app.config import AVATAR_PUBLIC_BASE_URL, AVATAR_SIZE, PUBLIC_API_URL


AVATAR_KEY_PATTERN = re.compile(
    r"^avatars/(?P<user_id>[0-9a-f-]{36})/(?P<avatar_id>[0-9a-f-]{36})\.webp$"
)
MAX_SOURCE_PIXELS = 25_000_000


class InvalidAvatarError(ValueError):
    pass


def avatar_url_from_key(object_key: str) -> str | None:
    match = AVATAR_KEY_PATTERN.fullmatch(object_key)
    if not match:
        return None
    if AVATAR_PUBLIC_BASE_URL:
        return f"{AVATAR_PUBLIC_BASE_URL}/{object_key}"
    return (
        f"{PUBLIC_API_URL}/api/avatars/{match.group('user_id')}/"
        f"{match.group('avatar_id')}.webp"
    )


def normalize_avatar(raw: bytes) -> bytes:
    try:
        with Image.open(io.BytesIO(raw)) as candidate:
            width, height = candidate.size
            if width <= 0 or height <= 0 or width * height > MAX_SOURCE_PIXELS:
                raise InvalidAvatarError("Avatar image dimensions are too large")
            candidate.verify()
        with Image.open(io.BytesIO(raw)) as source:
            image = ImageOps.exif_transpose(source)
            image.load()
            if image.mode in ("RGBA", "LA") or (
                image.mode == "P" and "transparency" in image.info
            ):
                image = image.convert("RGBA")
            else:
                image = image.convert("RGB")
            image = ImageOps.fit(
                image,
                (AVATAR_SIZE, AVATAR_SIZE),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )
            output = io.BytesIO()
            image.save(output, format="WEBP", quality=85, method=6)
            return output.getvalue()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise InvalidAvatarError("File is not a valid supported image") from exc
