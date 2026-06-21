import base64
import hashlib
import hmac
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()


def _verify_password(plain_password: str, stored_hash_b64: str) -> bool:
    try:
        decoded = base64.b64decode(stored_hash_b64)
    except Exception:
        return False
    if len(decoded) <= 32:
        return False
    salt = decoded[:32]
    digest = decoded[32:]
    new_digest = hashlib.pbkdf2_hmac("sha256", plain_password.encode(), salt, 100_000)
    return hmac.compare_digest(new_digest, digest)


@router.post("/internal/auth/login", response_model=UserResponse)
async def internal_login(payload: dict, session: AsyncSession = Depends(get_session)):
    # Accepts JSON: {"username_or_email": "...", "password": "..."}
    username_or_email = payload.get("username_or_email")
    password = payload.get("password")
    if not username_or_email or not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing credentials")

    result = await session.execute(
        select(User).where((User.username == username_or_email) | (User.email == username_or_email))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not _verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return user
