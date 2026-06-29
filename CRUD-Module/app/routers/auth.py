import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies.internal import require_internal_api_key
from app.models.user import User
from app.schemas.auth import (
    EmailLookupRequest,
    InternalAvatarUpdate,
    InternalProfileUpdate,
    InternalLoginRequest,
    PasswordChangeRequest,
    UserStatusUpdate,
)
from app.schemas.user import UserResponse
from app.security.passwords import hash_password, verify_password

router = APIRouter(
    prefix="/internal",
    tags=["internal-auth"],
    dependencies=[Depends(require_internal_api_key)],
)


@router.post("/auth/login", response_model=UserResponse)
async def internal_login(
    payload: InternalLoginRequest,
    session: AsyncSession = Depends(get_session),
) -> User:
    identity = payload.username_or_email.strip().lower()
    result = await session.execute(
        select(User).where(
            (func.lower(User.username) == identity)
            | (func.lower(User.email) == identity)
        )
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    return user


@router.post("/users/by-email", response_model=UserResponse)
async def get_user_by_email(
    payload: EmailLookupRequest,
    session: AsyncSession = Depends(get_session),
) -> User:
    user = await session.scalar(
        select(User).where(func.lower(User.email) == str(payload.email).strip().lower())
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.patch("/auth/change-password")
async def change_password(
    payload: PasswordChangeRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    user = await session.get(User, payload.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    if verify_password(payload.new_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    user.password_hash = hash_password(payload.new_password)
    await session.commit()
    return {"message": "Password updated successfully"}


@router.patch("/users/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: uuid.UUID,
    payload: UserStatusUpdate,
    session: AsyncSession = Depends(get_session),
) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if user.role == "admin" and not payload.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The administrator account cannot be disabled",
        )
    user.is_active = payload.is_active
    await session.commit()
    await session.refresh(user)
    return user


@router.patch("/users/{user_id}/profile", response_model=UserResponse)
async def update_user_profile(
    user_id: uuid.UUID,
    payload: InternalProfileUpdate,
    session: AsyncSession = Depends(get_session),
) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    user.first_name = payload.first_name
    user.last_name = payload.last_name
    await session.commit()
    await session.refresh(user)
    return user


@router.patch("/users/{user_id}/avatar", response_model=UserResponse)
async def update_user_avatar(
    user_id: uuid.UUID,
    payload: InternalAvatarUpdate,
    session: AsyncSession = Depends(get_session),
) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    user.avatar_key = payload.avatar_key
    await session.commit()
    await session.refresh(user)
    return user
