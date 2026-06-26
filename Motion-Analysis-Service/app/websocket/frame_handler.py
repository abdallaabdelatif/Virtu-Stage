from __future__ import annotations

from app.config import live_preview_enabled
from app.websocket.frame_session import create_frame_router

router = create_frame_router(live_preview=live_preview_enabled())
