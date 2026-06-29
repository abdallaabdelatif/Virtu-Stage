import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from app.security.passwords import validate_password_strength


class InternalLoginRequest(BaseModel):
    username_or_email: str
    password: str


class EmailLookupRequest(BaseModel):
    email: EmailStr


class PasswordResetTokenCreate(BaseModel):
    user_id: uuid.UUID
    token_hash: str
    expires_at: datetime


class PasswordResetRequest(BaseModel):
    token_hash: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        validate_password_strength(value)
        return value


class PasswordChangeRequest(BaseModel):
    user_id: uuid.UUID
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        validate_password_strength(value)
        return value


class UserStatusUpdate(BaseModel):
    is_active: bool


class InternalProfileUpdate(BaseModel):
    first_name: str
    last_name: str

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_required_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class InternalAvatarUpdate(BaseModel):
    avatar_key: str

    @field_validator("avatar_key")
    @classmethod
    def validate_avatar_key(cls, value: str) -> str:
        value = value.strip()
        if not value.startswith("avatars/") or not value.endswith(".webp"):
            raise ValueError("invalid avatar object key")
        return value


class MessageResponse(BaseModel):
    message: str
