from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def live_preview_enabled() -> bool:
    """Live OpenCV overlay during frame ingest. Set MOTION_LIVE_PREVIEW=0 on headless servers."""
    return os.getenv("MOTION_LIVE_PREVIEW", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )
