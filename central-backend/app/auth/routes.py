import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.deps import get_current_active_user
from app.auth.schemas import (
    AuthResponse,
    ForgotPasswordRequest,
    MessageResponse,
    ResetPasswordRequest,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.clients.crud_client import crud_client
from app.auth.jwt import create_access_token
from app.config import (
    ENVIRONMENT,
    FRONTEND_URL,
    PASSWORD_RESET_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)


def _http_error_detail(exc: httpx.HTTPStatusError, fallback: str) -> str:
    try:
        detail = exc.response.json().get("detail")
        return detail if isinstance(detail, str) else fallback
    except ValueError:
        return fallback


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(payload: UserRegister):
    try:
        user = await crud_client.create_user(payload.model_dump())
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=_http_error_detail(exc, "Unable to create account"),
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="CRUD service is unavailable",
        ) from exc

    access_token = create_access_token(
        subject=str(user["user_id"]),
        username=user["username"],
    )
    return AuthResponse(access_token=access_token, user=user)


@router.post("/login", response_model=AuthResponse)
async def login(payload: UserLogin):
    verify_payload = {
        "username_or_email": payload.username_or_email,
        "password": payload.password,
    }
    try:
        user = await crud_client.login_verify(verify_payload)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in (401, 403):
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=_http_error_detail(exc, "Invalid credentials"),
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="CRUD service is unavailable",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="CRUD service is unavailable",
        ) from exc

    access_token = create_access_token(subject=str(user["user_id"]), username=user["username"])
    return AuthResponse(access_token=access_token, user=user)


@router.get("/me", response_model=UserResponse)
async def current_user(user=Depends(get_current_active_user)):
    return user


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(payload: ForgotPasswordRequest):
    response = {
        "message": (
            "If an account exists for this email, a reset link has been sent."
        )
    }
    try:
        user = await crud_client.get_user_by_email(
            payload.email.lower().strip()
        )
        if not user or not user.get("is_active", False):
            return response

        plaintext_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(
            plaintext_token.encode("utf-8")
        ).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=PASSWORD_RESET_EXPIRE_MINUTES
        )
        await crud_client.store_password_reset_token(
            {
                "user_id": user["user_id"],
                "token_hash": token_hash,
                "expires_at": expires_at.isoformat(),
            }
        )

        if ENVIRONMENT == "development":
            logger.warning(
                "Development password reset URL: %s/reset-password?token=%s",
                FRONTEND_URL,
                plaintext_token,
            )
    except httpx.HTTPError:
        logger.exception("Unable to create password reset request")

    return response


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(payload: ResetPasswordRequest):
    token_hash = hashlib.sha256(payload.token.encode("utf-8")).hexdigest()
    try:
        result = await crud_client.reset_password(
            token_hash, payload.new_password
        )
        return result
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in (400, 404, 422):
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=_http_error_detail(
                    exc, "Reset token is invalid or expired"
                ),
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="CRUD service is unavailable",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="CRUD service is unavailable",
        ) from exc
