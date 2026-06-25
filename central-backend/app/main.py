from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.auth.routes import router as auth_router
from app.api.protected import router as protected_router
from app.api.vr import router as vr_router
from app.auth.jwt import verify_token
from app.clients.crud_client import crud_client


app = FastAPI(title="Central Backend")


# Paths that do not require authentication
# TODO: Remove VR endpoints (/sessions, /ws/vr) from public paths after testing phase is complete
_PUBLIC_PATH_PREFIXES = ("/auth", "/docs", "/openapi.json", "/redoc", "/", "/voice-analyses", "/sessions", "/ws/vr")


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    # allow public prefixes
    if any(path.startswith(p) for p in _PUBLIC_PATH_PREFIXES):
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
    except Exception:
        return JSONResponse({"detail": "Invalid authentication credentials"}, status_code=401)

    return await call_next(request)


app.include_router(auth_router, prefix="")
app.include_router(vr_router)
app.include_router(protected_router)


@app.get("/")
async def root():
    return {"message": "central-backend running"}
