from datetime import datetime
import re
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator
from app.auth.passwords import validate_password_strength
from app.services.avatars import avatar_url_from_key


USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 30
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._]*$")


def validate_and_normalize_username(value: str) -> str:
    value = value.strip()
    if not USERNAME_MIN_LENGTH <= len(value) <= USERNAME_MAX_LENGTH:
        raise ValueError(
            f"username must be between {USERNAME_MIN_LENGTH} and "
            f"{USERNAME_MAX_LENGTH} characters"
        )
    if not USERNAME_PATTERN.fullmatch(value):
        raise ValueError(
            "username must start with a letter or number and contain only "
            "letters, numbers, dots, or underscores"
        )
    return value


def normalize_email(value: EmailStr) -> str:
    return str(value).strip().lower()


class UserRegister(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    gender: Optional[Literal["male", "female"]] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        return validate_and_normalize_username(value)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: EmailStr) -> str:
        return normalize_email(value)

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        validate_password_strength(value)
        return value


class UserLogin(BaseModel):
    username_or_email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    username: str


class UserResponse(BaseModel):
    user_id: UUID
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    gender: Optional[str] = None
    avatar_key: Optional[str] = Field(default=None, exclude=True)
    avatar_url: Optional[str] = None
    role: Literal["user", "admin"]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def populate_avatar_url(self):
        if self.avatar_key:
            self.avatar_url = avatar_url_from_key(self.avatar_key)
        return self


class AuthResponse(Token):
    user: UserResponse


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        validate_password_strength(value)
        return value


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        validate_password_strength(value)
        return value


class UserStatusRequest(BaseModel):
    is_active: bool


class ProfileUpdateRequest(BaseModel):
    first_name: str
    last_name: str

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_required_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class MessageResponse(BaseModel):
    message: str
