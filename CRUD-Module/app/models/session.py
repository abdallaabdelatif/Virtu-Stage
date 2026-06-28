import uuid
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid
from sqlalchemy import Enum as SAEnum
from ..database import Base


class ScenarioType(str, enum.Enum):
    interview = "interview"
    public_speaking = "public_speaking"


class DifficultyLevel(str, enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class SessionStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class TrainingSession(Base):
    __tablename__ = "training_sessions"

    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    scenario_type: Mapped[ScenarioType] = mapped_column(
        SAEnum(ScenarioType), nullable=False
    )
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(
        SAEnum(DifficultyLevel), nullable=False
    )
    status: Mapped[SessionStatus] = mapped_column(
        SAEnum(SessionStatus), nullable=False, default=SessionStatus.pending
    )

    start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    voice_analysis_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    motion_analysis_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="training_sessions")

    conversation_history: Mapped[Optional["ConversationHistory"]] = relationship(
        "ConversationHistory", back_populates="session", uselist=False
    )

    voice_analysis: Mapped[Optional["VoiceAnalysis"]] = relationship(
        "VoiceAnalysis", back_populates="session", uselist=False
    )

    motion_analysis: Mapped[Optional["MotionAnalysis"]] = relationship(
        "MotionAnalysis", back_populates="session", uselist=False
    )
