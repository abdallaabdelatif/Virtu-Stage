import uuid
from datetime import datetime

from pydantic import BaseModel


class ScoreHistoryPoint(BaseModel):
    session_id: uuid.UUID
    date: str
    score: float


class AnalysisHistoryPoint(BaseModel):
    session_id: uuid.UUID
    label: str
    voice_score: float
    motion_score: float


class UserDashboardAggregate(BaseModel):
    total_sessions: int
    analyzed_sessions: int
    average_overall_score: float | None
    improvement_rate: float | None
    score_history: list[ScoreHistoryPoint]
    analysis_history: list[AnalysisHistoryPoint]


class SessionsByDayPoint(BaseModel):
    date: str
    count: int


class AverageScoreByMonthPoint(BaseModel):
    month: str
    score: float


class RecentRegistration(BaseModel):
    user_id: uuid.UUID
    name: str
    email: str
    created_at: datetime


class AdminDashboardAggregate(BaseModel):
    total_users: int
    total_sessions: int
    platform_average_score: float | None
    sessions_today: int
    sessions_by_day: list[SessionsByDayPoint]
    average_score_by_month: list[AverageScoreByMonthPoint]
    recent_registrations: list[RecentRegistration]


class AdminUserSummary(BaseModel):
    user_id: uuid.UUID
    name: str
    email: str
    role: str
    is_active: bool
    session_count: int
    created_at: datetime
