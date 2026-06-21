import logging
from fastapi import FastAPI
from app.websocket.audio_handler import router as audio_router
from app.websocket.transcript_handler import router as transcript_router

logging.basicConfig(level=logging.INFO)

app = FastAPI()

app.include_router(audio_router)
app.include_router(transcript_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "voice analysis service started"}
