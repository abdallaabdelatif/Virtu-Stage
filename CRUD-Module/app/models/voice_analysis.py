import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
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

    confidence_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    anxiety_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    clarity_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    focus_level: Mapped[float | None] = mapped_column(Float, nullable=True)

    confidence_reasons: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )
    anxiety_reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    clarity_reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    focus_reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    voice_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    voice_quality_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    fluency_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    fluency_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    energy_control_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    energy_control_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    articulation_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    articulation_level: Mapped[str | None] = mapped_column(String(32), nullable=True)

    words_per_minute: Mapped[float | None] = mapped_column(Float, nullable=True)
    pause_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    filler_word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pause_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    longest_pause_sec: Mapped[float | None] = mapped_column(Float, nullable=True)

    confidence_feedback: Mapped[str] = mapped_column(Text, nullable=False, default="")
    anxiety_feedback: Mapped[str] = mapped_column(Text, nullable=False, default="")
    clarity_feedback: Mapped[str] = mapped_column(Text, nullable=False, default="")
    focus_feedback: Mapped[str] = mapped_column(Text, nullable=False, default="")

    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    session: Mapped["TrainingSession"] = relationship(
        "TrainingSession", back_populates="voice_analysis"
    )
