import logging

from fastapi import FastAPI

from app.websocket.frame_handler import router as frame_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="VirtuStage Motion Analysis Service")

app.include_router(frame_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "motion analysis service started",
        "input": "websocket",
        "endpoint": "/ws/motion-analysis/frames/{session_id}",
    }
