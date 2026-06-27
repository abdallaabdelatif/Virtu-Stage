from __future__ import annotations

import argparse
import logging

import uvicorn
from fastapi import FastAPI

from app.config import live_preview_enabled, set_live_preview_override
from app.websocket.frame_session import create_frame_router

logging.basicConfig(level=logging.INFO)


def build_app(*, live_preview: bool | None = None) -> FastAPI:
    if live_preview is not None:
        set_live_preview_override(live_preview)

    preview_on = live_preview_enabled()
    app = FastAPI(title="VirtuStage Motion Analysis Service")
    app.include_router(create_frame_router(live_preview=preview_on))

    @app.get("/")
    async def root() -> dict[str, str]:
        return {
            "message": "motion analysis service started",
            "input": "websocket",
            "endpoint": "/ws/motion-analysis/frames/{session_id}",
            "live_preview": preview_on,
            "preview_hint": (
                "Run with: python -m app.main --preview"
                if not preview_on
                else "OpenCV window on this machine; press Q to hide"
            ),
        }

    return app


app = build_app()


def main() -> None:
    parser = argparse.ArgumentParser(description="VirtuStage Motion Analysis Service")
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Show live OpenCV overlay while WebSocket frames arrive",
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9001)
    args = parser.parse_args()
    uvicorn.run(build_app(live_preview=args.preview), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
