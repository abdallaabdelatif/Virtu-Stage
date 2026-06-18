import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, field_validator


class ConversationTurn(BaseModel):
    role: Literal["interviewer", "user"]
    content: str


class ConversationHistoryCreate(BaseModel):
    session_id: uuid.UUID
    turns: list[ConversationTurn] = []


class ConversationHistoryUpdate(BaseModel):
    turns: list[ConversationTurn]

    @field_validator("turns")
    @classmethod
    def turns_not_empty(cls, v: list[ConversationTurn]) -> list[ConversationTurn]:
        if not v:
            raise ValueError("turns cannot be empty on update")
        return v


class ConversationHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    conversation_id: uuid.UUID
    session_id: uuid.UUID
    turns: list[ConversationTurn]
    created_at: datetime
    updated_at: datetime
