from __future__ import annotations
from fastapi import FastAPI, HTTPException
from app.websocket.audio_handler import router as audio_router
from app.websocket.session_completion import get_session_analysis
from app.websocket.transcript_handler import router as transcript_router


app = FastAPI()

app.include_router(audio_router)
app.include_router(transcript_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/sessions/{session_id}/analysis")
async def session_analysis(session_id: str) -> dict:
    result = await get_session_analysis(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="session_not_found")
    return result
