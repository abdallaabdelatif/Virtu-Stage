import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.conversation_history import ConversationHistory
from app.schemas.conversation_history import (
    ConversationHistoryCreate,
    ConversationHistoryResponse,
    ConversationHistoryUpdate,
)

router = APIRouter(prefix="/conversations", tags=["conversation-history"])


@router.post(
    "", response_model=ConversationHistoryResponse, status_code=status.HTTP_201_CREATED
)
async def create_conversation(
    payload: ConversationHistoryCreate,
    db: AsyncSession = Depends(get_session),
) -> ConversationHistory:
    existing = await db.scalar(
        select(ConversationHistory).where(
            ConversationHistory.session_id == payload.session_id
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A conversation history already exists for this session",
        )

    conversation = ConversationHistory(
        session_id=payload.session_id,
        turns=[turn.model_dump() for turn in payload.turns],
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


@router.get("/{conversation_id}", response_model=ConversationHistoryResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> ConversationHistory:
    conversation = await db.get(ConversationHistory, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )
    return conversation


@router.get("/session/{session_id}", response_model=ConversationHistoryResponse)
async def get_conversation_by_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> ConversationHistory:
    conversation = await db.scalar(
        select(ConversationHistory).where(ConversationHistory.session_id == session_id)
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )
    return conversation


@router.put("/{conversation_id}", response_model=ConversationHistoryResponse)
async def update_conversation(
    conversation_id: uuid.UUID,
    payload: ConversationHistoryUpdate,
    db: AsyncSession = Depends(get_session),
) -> ConversationHistory:
    conversation = await db.get(ConversationHistory, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )

    conversation.turns = [turn.model_dump() for turn in payload.turns]
    await db.commit()
    await db.refresh(conversation)
    return conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> None:
    conversation = await db.get(ConversationHistory, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )

    await db.delete(conversation)
    await db.commit()
