import uuid
import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from app.security.passwords import validate_password_strength


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


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    gender: Optional[str] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        return validate_and_normalize_username(value)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: EmailStr) -> str:
        return normalize_email(value)

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in {"male", "female", "other"}:
            raise ValueError("gender must be 'male', 'female', or 'other'")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        validate_password_strength(value)
        return value


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: Optional[str]) -> Optional[str]:
        return validate_and_normalize_username(value) if value is not None else None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: Optional[EmailStr]) -> Optional[str]:
        return normalize_email(value) if value is not None else None

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in {"male", "female", "other"}:
            raise ValueError("gender must be 'male', 'female', or 'other'")
        return v


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    username: str
    email: str
    first_name: str
    last_name: str
    gender: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
