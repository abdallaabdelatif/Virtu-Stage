from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import mean

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import SessionStatus, TrainingSession
from app.models.user import User
from app.schemas.dashboard import (
    AdminDashboardAggregate,
    AdminUserSummary,
    AnalysisHistoryPoint,
    AverageScoreByMonthPoint,
    RecentRegistration,
    ScoreHistoryPoint,
    SessionsByDayPoint,
    UserDashboardAggregate,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _format_label(value: datetime) -> str:
    return _as_utc(value).strftime("%b %d")


def _calculate_improvement(scores: list[float]) -> float | None:
    if len(scores) < 10:
        return None
    recent = scores[:5]
    previous = scores[5:10]
    if not recent or not previous:
        return None
    previous_average = mean(previous)
    if previous_average == 0:
        return None
    recent_average = mean(recent)
    return round(((recent_average - previous_average) / previous_average) * 100, 2)


async def get_user_dashboard(
    db: AsyncSession, user_id: uuid.UUID
) -> UserDashboardAggregate:
    total_sessions = await db.scalar(
        select(func.count())
        .select_from(TrainingSession)
        .where(TrainingSession.user_id == user_id)
    )
    total_sessions = int(total_sessions or 0)

    completed_result = await db.execute(
        select(TrainingSession)
        .where(
            TrainingSession.user_id == user_id,
            TrainingSession.status == SessionStatus.completed,
            TrainingSession.overall_score.is_not(None),
        )
        .order_by(TrainingSession.end_time.desc(), TrainingSession.created_at.desc())
    )
    completed_sessions = list(completed_result.scalars().all())
    analyzed_sessions = len(completed_sessions)

    average_overall_score = (
        round(mean(s.overall_score for s in completed_sessions), 2)
        if completed_sessions
        else None
    )

    improvement_rate = _calculate_improvement(
        [float(s.overall_score) for s in completed_sessions if s.overall_score is not None]
    )

    score_history = [
        ScoreHistoryPoint(
            session_id=session.session_id,
            date=_as_utc(session.end_time or session.created_at).date().isoformat(),
            score=float(session.overall_score),
        )
        for session in completed_sessions[:30]
    ]

    analysis_result = await db.execute(
        select(TrainingSession)
        .where(
            TrainingSession.user_id == user_id,
            TrainingSession.status == SessionStatus.completed,
            TrainingSession.voice_analysis_score.is_not(None),
            TrainingSession.motion_analysis_score.is_not(None),
        )
        .order_by(TrainingSession.end_time.desc(), TrainingSession.created_at.desc())
        .limit(10)
    )
    analysis_sessions = list(analysis_result.scalars().all())
    analysis_history = [
        AnalysisHistoryPoint(
            session_id=session.session_id,
            label=_format_label(session.end_time or session.created_at),
            voice_score=float(session.voice_analysis_score),
            motion_score=float(session.motion_analysis_score),
        )
        for session in reversed(analysis_sessions)
    ]

    return UserDashboardAggregate(
        total_sessions=total_sessions,
        analyzed_sessions=analyzed_sessions,
        average_overall_score=average_overall_score,
        improvement_rate=improvement_rate,
        score_history=score_history,
        analysis_history=analysis_history,
    )


async def get_admin_dashboard(db: AsyncSession) -> AdminDashboardAggregate:
    total_users = int(await db.scalar(select(func.count()).select_from(User)) or 0)
    total_sessions = int(
        await db.scalar(select(func.count()).select_from(TrainingSession)) or 0
    )

    platform_average_score = await db.scalar(
        select(func.avg(TrainingSession.overall_score)).where(
            TrainingSession.status == SessionStatus.completed,
            TrainingSession.overall_score.is_not(None),
        )
    )
    platform_average_score = (
        round(float(platform_average_score), 2)
        if platform_average_score is not None
        else None
    )

    today = _utc_now().date()
    today_start = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
    tomorrow_start = today_start + timedelta(days=1)
    sessions_today = int(
        await db.scalar(
            select(func.count())
            .select_from(TrainingSession)
            .where(
                TrainingSession.created_at >= today_start,
                TrainingSession.created_at < tomorrow_start,
            )
        )
        or 0
    )

    sessions_result = await db.execute(
        select(TrainingSession.created_at).order_by(TrainingSession.created_at.desc())
    )
    day_counts: dict[str, int] = defaultdict(int)
    for (created_at,) in sessions_result.all():
        day_counts[_as_utc(created_at).date().isoformat()] += 1
    sessions_by_day = [
        SessionsByDayPoint(date=day, count=count)
        for day, count in sorted(day_counts.items(), reverse=True)[:14]
    ]
    sessions_by_day.reverse()

    completed_result = await db.execute(
        select(TrainingSession.end_time, TrainingSession.created_at, TrainingSession.overall_score).where(
            TrainingSession.status == SessionStatus.completed,
            TrainingSession.overall_score.is_not(None),
        )
    )
    month_scores: dict[str, list[float]] = defaultdict(list)
    for end_time, created_at, overall_score in completed_result.all():
        timestamp = end_time or created_at
        month_key = _as_utc(timestamp).strftime("%Y-%m")
        month_scores[month_key].append(float(overall_score))
    average_score_by_month = [
        AverageScoreByMonthPoint(
            month=month,
            score=round(mean(scores), 2),
        )
        for month, scores in sorted(month_scores.items())
    ][-12:]

    users_result = await db.execute(
        select(User).order_by(User.created_at.desc()).limit(5)
    )
    recent_registrations = [
        RecentRegistration(
            user_id=user.user_id,
            name=f"{user.first_name} {user.last_name}".strip(),
            email=user.email,
            created_at=user.created_at,
        )
        for user in users_result.scalars().all()
    ]

    return AdminDashboardAggregate(
        total_users=total_users,
        total_sessions=total_sessions,
        platform_average_score=platform_average_score,
        sessions_today=sessions_today,
        sessions_by_day=sessions_by_day,
        average_score_by_month=average_score_by_month,
        recent_registrations=recent_registrations,
    )


async def list_admin_users(db: AsyncSession) -> list[AdminUserSummary]:
    counts_result = await db.execute(
        select(TrainingSession.user_id, func.count())
        .group_by(TrainingSession.user_id)
    )
    session_counts = {row[0]: row[1] for row in counts_result.all()}

    users_result = await db.execute(
        select(User).order_by(User.created_at.desc())
    )
    return [
        AdminUserSummary(
            user_id=user.user_id,
            name=f"{user.first_name} {user.last_name}".strip(),
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            session_count=int(session_counts.get(user.user_id, 0)),
            created_at=user.created_at,
        )
        for user in users_result.scalars().all()
    ]
