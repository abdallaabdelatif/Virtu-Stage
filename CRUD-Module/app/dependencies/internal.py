import os

from fastapi import Header, HTTPException, status


INTERNAL_API_KEY = os.getenv(
    "INTERNAL_API_KEY", "development-internal-key-change-me"
)
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()

if ENVIRONMENT == "production" and (
    INTERNAL_API_KEY == "development-internal-key-change-me"
    or len(INTERNAL_API_KEY) < 32
):
    raise RuntimeError("INTERNAL_API_KEY must be a unique secret of at least 32 characters")


async def require_internal_api_key(
    x_internal_api_key: str | None = Header(default=None),
) -> None:
    if not x_internal_api_key or x_internal_api_key != INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal service credentials",
        )
