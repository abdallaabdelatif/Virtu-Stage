from fastapi import APIRouter, Depends
from app.auth.deps import get_current_user

router = APIRouter(prefix="/protected", tags=["protected"])


@router.get("")
async def protected_endpoint(current_user=Depends(get_current_user)):
    return {"message": "authorized", "user_id": current_user["user_id"], "username": current_user["username"]}
