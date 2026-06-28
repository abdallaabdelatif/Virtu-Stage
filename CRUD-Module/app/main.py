from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import Base, engine
from app.routers import user as user_router
from app.routers import session as session_router
from app.routers import conversation_history as conversation_history_router
from app.routers import voice_analysis as voice_analysis_router
from app.routers import motion_analysis as motion_analysis_router
from app.routers import auth as auth_router
from app.routers import password_reset as password_reset_router
from app.routers import aggregates as aggregates_router
from app.routers import library_file as library_file_router
from app.migrations import run_migrations

from app.models import user as user_model
from app.models import session as session_model
from app.models import conversation_history as conversation_history_model
from app.models import voice_analysis as voice_analysis_model
from app.models import motion_analysis as motion_analysis_model
from app.models import password_reset_token as password_reset_token_model
from app.models import library_file as library_file_model
from app.models import presentation_slide as presentation_slide_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await run_migrations(conn)
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(user_router.router)
app.include_router(session_router.router)
app.include_router(conversation_history_router.router)
app.include_router(voice_analysis_router.router)
app.include_router(motion_analysis_router.router)
app.include_router(auth_router.router)
app.include_router(password_reset_router.router)
app.include_router(aggregates_router.router)
app.include_router(library_file_router.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Server started successfully"}
