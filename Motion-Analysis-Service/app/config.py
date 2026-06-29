from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

CENTRALIZED_BACKEND_URL = os.getenv("CENTRALIZED_BACKEND_URL", "http://localhost:9000")
INTERNAL_API_KEY = os.getenv(
    "INTERNAL_API_KEY", "development-internal-key-change-me"
)
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()

if ENVIRONMENT == "production" and (
    INTERNAL_API_KEY == "development-internal-key-change-me"
    or len(INTERNAL_API_KEY) < 32
):
    raise RuntimeError("INTERNAL_API_KEY must be a unique secret of at least 32 characters")

_preview_override: bool | None = None


def set_live_preview_override(value: bool | None) -> None:
    global _preview_override
    _preview_override = value


def live_preview_enabled() -> bool:
    """
    Live OpenCV overlay during WebSocket frame ingest.

    Off by default. Enable with:
      - `python -m app.main --preview`
      - or MOTION_LIVE_PREVIEW=1 in .env
    """
    if _preview_override is not None:
        return _preview_override
    return os.getenv("MOTION_LIVE_PREVIEW", "0").strip().lower() in (
        "1",
        "true",
        "yes",
    )
