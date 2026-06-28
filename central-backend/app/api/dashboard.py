from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas.dashboard import (
    AdminDashboardResponse,
    AdminUserResponse,
    UserDashboardResponse,
)
from app.auth.deps import get_current_active_user, require_admin
from app.clients.crud_client import crud_client

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/me", response_model=UserDashboardResponse)
async def get_my_dashboard(user=Depends(get_current_active_user)):
    try:
        data = await crud_client.get_user_dashboard(str(user["user_id"]))
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="CRUD service is unavailable",
        ) from exc
    return UserDashboardResponse(**data)
