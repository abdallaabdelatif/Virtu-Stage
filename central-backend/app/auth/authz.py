from uuid import UUID

from fastapi import HTTPException, status


def require_resource_owner(
    resource_owner_id: str | UUID,
    current_user: dict,
) -> None:
    if str(resource_owner_id) != str(current_user["user_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )
