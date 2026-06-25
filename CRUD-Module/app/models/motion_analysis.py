import uuid
import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid
from sqlalchemy import Enum as SAEnum
from app.database import Base


class FidgetingLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class MotionAnalysis(Base):
    __tablename__ = "motion_analysis"

    motion_analysis_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("training_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    head_stability_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    head_movement_variance: Mapped[float] = mapped_column(
        Numeric(10, 4), nullable=False
    )
    head_angle: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    head_avg_velocity: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)

    fidgeting_level: Mapped[FidgetingLevel] = mapped_column(
        SAEnum(FidgetingLevel), nullable=False
    )
    fidgeting_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)

    sudden_index: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    repetitive_index: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)

    hand_movement_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    left_hand_avg_velocity: Mapped[float] = mapped_column(
        Numeric(10, 4), nullable=False
    )
    right_hand_avg_velocity: Mapped[float] = mapped_column(
        Numeric(10, 4), nullable=False
    )

    posture_quality: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    posture_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)

    nervousness_indicator: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    motion_overall_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)

    presentation_assessment: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    recommendations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    dominant_posture_type: Mapped[str | None] = mapped_column(nullable=True)
    session_metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    session: Mapped["TrainingSession"] = relationship(
        "TrainingSession", back_populates="motion_analysis"
    )
