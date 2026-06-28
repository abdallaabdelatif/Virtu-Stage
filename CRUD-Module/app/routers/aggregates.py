import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies.internal import require_internal_api_key
from app.schemas.dashboard import (
    AdminDashboardAggregate,
    AdminUserSummary,
    UserDashboardAggregate,
)
from app.services.dashboard_aggregates import (
    get_admin_dashboard,
    get_user_dashboard,
    list_admin_users,
)

router = APIRouter(prefix="/aggregates", tags=["aggregates"])


@router.get("/users/{user_id}/dashboard", response_model=UserDashboardAggregate)
async def user_dashboard_aggregate(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    _internal_access: None = Depends(require_internal_api_key),
) -> UserDashboardAggregate:
    return await get_user_dashboard(db, user_id)


@router.get("/admin/dashboard", response_model=AdminDashboardAggregate)
async def admin_dashboard_aggregate(
    db: AsyncSession = Depends(get_session),
    _internal_access: None = Depends(require_internal_api_key),
) -> AdminDashboardAggregate:
    return await get_admin_dashboard(db)


@router.get("/admin/users", response_model=list[AdminUserSummary])
async def admin_users_aggregate(
    db: AsyncSession = Depends(get_session),
    _internal_access: None = Depends(require_internal_api_key),
) -> list[AdminUserSummary]:
    return await list_admin_users(db)
