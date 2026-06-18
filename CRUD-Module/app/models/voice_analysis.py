import uuid
import enum
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid
from sqlalchemy import Enum as SAEnum
from app.database import Base


class DominantEmotion(str, enum.Enum):
    neutral = "neutral"
    happy = "happy"
    sad = "sad"
    angry = "angry"


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

    emotion_neutral: Mapped[float] = mapped_column(Float, nullable=False)
    emotion_happy: Mapped[float] = mapped_column(Float, nullable=False)
    emotion_sad: Mapped[float] = mapped_column(Float, nullable=False)
    emotion_angry: Mapped[float] = mapped_column(Float, nullable=False)

    dominant_emotion: Mapped[DominantEmotion] = mapped_column(
        SAEnum(DominantEmotion), nullable=False
    )

    anxiety_level: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    clarity_level: Mapped[float] = mapped_column(Float, nullable=False)
    focus_score: Mapped[float] = mapped_column(Float, nullable=False)

    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    session: Mapped["TrainingSession"] = relationship(
        "TrainingSession", back_populates="voice_analysis"
    )
