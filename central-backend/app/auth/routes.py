from fastapi import APIRouter, HTTPException, status, Depends
from app.auth.schemas import UserRegister, UserLogin, Token
from app.clients.crud_client import crud_client
from app.auth.jwt import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister):
    # Forward user creation to CRUD service
    try:
        user = await crud_client.create_user(payload.model_dump())
        return user
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/login", response_model=Token)
async def login(payload: UserLogin):
    # call CRUD to verify credentials
    verify_payload = {
        "username_or_email": payload.username_or_email,
        "password": payload.password,
    }
    user = await crud_client.login_verify(verify_payload)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(subject=str(user["user_id"]), username=user["username"])
    return Token(access_token=access_token)
