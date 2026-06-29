from fastapi import FastAPI, Request
import httpx
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.auth.routes import router as auth_router
from app.api.protected import router as protected_router
from app.api.account import router as account_router
from app.api.admin import router as admin_router
from app.api.dashboard import router as dashboard_router
from app.api.sessions import router as sessions_router
from app.api.files import router as files_router
from app.api.vr import router as vr_router
from app.auth.jwt import verify_token
from app.clients.crud_client import crud_client
from app.config import CORS_ORIGINS


app = FastAPI(title="Central Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exact paths that do not require authentication.
_PUBLIC_PATHS = {
    "/",
    "/docs",
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/forgot-password",
    "/api/auth/reset-password",
    "/health",
    "/voice-analyses",
    "/motion-analyses",
    "/openapi.json",
}

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    is_public = (
        request.method == "OPTIONS"
        or path in _PUBLIC_PATHS
    )
    if is_public:
        return await call_next(request)

    auth = request.headers.get("authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)

    token = auth.split(" ", 1)[1]
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise Exception("invalid token payload")
        user = await crud_client.get_user(user_id)
        if not user:
            raise Exception("user not found")
        # attach user for downstream handlers (optional)
        request.state.user = user
    except httpx.HTTPError:
        return JSONResponse(
            {"detail": "CRUD service is unavailable"},
            status_code=502,
        )
    except Exception:
        return JSONResponse({"detail": "Invalid authentication credentials"}, status_code=401)

    return await call_next(request)


app.include_router(auth_router, prefix="")
app.include_router(vr_router)
app.include_router(sessions_router)
app.include_router(files_router)
app.include_router(dashboard_router)
app.include_router(protected_router)
app.include_router(account_router)
app.include_router(admin_router)


@app.get("/")
async def root():
    return {"message": "central-backend running"}


@app.get("/health")
async def health():
    return {"status": "ok"}
