import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.database import Base


class VoiceAnalysis(Base):
    __tablename__ = "voice_analysis"

    voice_analysis_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("training_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    anxiety_level: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    clarity_level: Mapped[float] = mapped_column(Float, nullable=False)
    focus_score: Mapped[float] = mapped_column(Float, nullable=False)

    pause_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    pause_count: Mapped[int] = mapped_column(Integer, nullable=False)
    longest_pause_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    filler_words_count: Mapped[int] = mapped_column(Integer, nullable=False)
    speech_rate_wpm: Mapped[float] = mapped_column(Float, nullable=False)

    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    session: Mapped["TrainingSession"] = relationship(
        "TrainingSession", back_populates="voice_analysis"
    )
