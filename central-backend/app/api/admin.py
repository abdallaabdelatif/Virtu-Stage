import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.deps import require_admin
from app.auth.routes import _http_error_detail
from app.auth.schemas import UserResponse, UserStatusRequest
from app.clients.crud_client import crud_client

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.patch(
    "/users/{user_id}/status",
    response_model=UserResponse,
)
async def update_user_status(
    user_id: str,
    payload: UserStatusRequest,
    admin=Depends(require_admin),
):
    if str(admin["user_id"]) == user_id and not payload.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot disable their own account",
        )
    try:
        return await crud_client.update_user_status(
            user_id, payload.is_active
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in (404, 422):
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=_http_error_detail(exc, "Unable to update user"),
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
