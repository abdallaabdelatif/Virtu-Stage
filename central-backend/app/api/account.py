import httpx
from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.auth.deps import get_current_active_user
from app.auth.routes import _http_error_detail
from app.auth.schemas import (
    ChangePasswordRequest,
    MessageResponse,
    ProfileUpdateRequest,
    UserResponse,
)
from app.clients.crud_client import crud_client

router = APIRouter(prefix="/api/users/me", tags=["account"])


@router.patch("", response_model=UserResponse)
async def update_profile(
    payload: ProfileUpdateRequest,
    user=Depends(get_current_active_user),
):
    try:
        return await crud_client.update_user_profile(
            str(user["user_id"]),
            payload.first_name,
            payload.last_name,
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in (403, 404, 422):
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=_http_error_detail(
                    exc, "Unable to update profile"
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


@router.patch("/password", response_model=MessageResponse)
async def change_password(
    payload: ChangePasswordRequest,
    user=Depends(get_current_active_user),
):
    try:
        return await crud_client.change_password(
            str(user["user_id"]),
            payload.current_password,
            payload.new_password,
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in (400, 401, 403, 404, 422):
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=_http_error_detail(
                    exc, "Unable to update password"
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


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(user=Depends(get_current_active_user)) -> Response:
    try:
        await crud_client.delete_user(str(user["user_id"]))
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
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
    return Response(status_code=status.HTTP_204_NO_CONTENT)
