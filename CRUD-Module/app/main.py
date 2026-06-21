from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import Base, engine
from app.routers import user as user_router
from app.routers import session as session_router
from app.routers import conversation_history as conversation_history_router
from app.routers import voice_analysis as voice_analysis_router
from app.routers import motion_analysis as motion_analysis_router
from app.routers import auth as auth_router

from app.models import user as user_model
from app.models import session as session_model
from app.models import conversation_history as conversation_history_model
from app.models import voice_analysis as voice_analysis_model
from app.models import motion_analysis as motion_analysis_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(user_router.router)
app.include_router(session_router.router)
app.include_router(conversation_history_router.router)
app.include_router(voice_analysis_router.router)
app.include_router(motion_analysis_router.router)
app.include_router(auth_router.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Server started successfully"}
