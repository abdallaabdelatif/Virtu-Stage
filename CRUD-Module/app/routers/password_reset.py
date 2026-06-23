from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies.internal import require_internal_api_key
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.schemas.auth import (
    MessageResponse,
    PasswordResetRequest,
    PasswordResetTokenCreate,
)
from app.security.passwords import hash_password

router = APIRouter(
    prefix="/internal/password-reset",
    tags=["internal-password-reset"],
    dependencies=[Depends(require_internal_api_key)],
)


@router.post("/request", response_model=MessageResponse)
async def store_reset_token(
    payload: PasswordResetTokenCreate,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    now = datetime.now(timezone.utc)
    user = await session.get(User, payload.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await session.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == payload.user_id,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    session.add(
        PasswordResetToken(
            user_id=payload.user_id,
            token_hash=payload.token_hash,
            expires_at=payload.expires_at,
        )
    )
    await session.commit()
    return {"message": "Reset token stored"}


@router.post("/reset", response_model=MessageResponse)
async def reset_password(
    payload: PasswordResetRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    now = datetime.now(timezone.utc)

    consume_result = await session.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.token_hash == payload.token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.revoked_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
        .values(used_at=now)
    )
    if consume_result.rowcount != 1:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token is invalid, expired, or already used",
        )

    token_record = await session.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == payload.token_hash
        )
    )
    if not token_record:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token is invalid",
        )

    user = await session.get(User, token_record.user_id)
    if not user:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token is invalid",
        )

    user.password_hash = hash_password(payload.new_password)
    await session.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user.user_id,
            PasswordResetToken.token_hash != payload.token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    await session.commit()
    return {"message": "Password reset successfully"}
