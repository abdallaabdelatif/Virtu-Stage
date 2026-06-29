import type {
  AdminDashboardDto,
  AdminUserDto,
  UserDashboardDto,
} from '../types/dashboard.dto';
import type { AdminDashboardData, UserDashboardData } from '../types/dashboard';
import type { ManagedUser } from '../types/admin';
import {
  formatPlatformCalendarDay,
  formatPlatformDate,
} from '../utils/dateTime';

function formatDateTime(value: string) {
  return formatPlatformDate(value, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function formatChartDay(value: string) {
  return formatPlatformCalendarDay(value, {
    month: 'short',
    day: 'numeric',
  });
}

function formatChartMonth(value: string) {
  const [year, month] = value.split('-');
  const date = new Date(Number(year), Number(month) - 1, 1);
  return date.toLocaleDateString('en-US', { month: 'short' });
}

export function mapUserDashboard(dto: UserDashboardDto): UserDashboardData {
  return {
    totalSessions: dto.total_sessions,
    analyzedSessions: dto.analyzed_sessions,
    avgScore: dto.average_overall_score,
    improvementRate: dto.improvement_rate,
    progressData: dto.score_history.map((point) => ({
      date: point.date,
      score: point.score,
    })),
    voiceMotionData: dto.analysis_history.map((point) => ({
      label: point.label,
      voice: point.voice_score,
      motion: point.motion_score,
    })),
  };
}

export function mapAdminDashboard(dto: AdminDashboardDto): AdminDashboardData {
  return {
    totalUsers: dto.total_users,
    totalSessions: dto.total_sessions,
    platformAvgScore: dto.platform_average_score,
    sessionsToday: dto.sessions_today,
    adminSessionsData: dto.sessions_by_day.map((point) => ({
      day: formatChartDay(point.date),
      sessions: point.count,
    })),
    adminScoreData: dto.average_score_by_month.map((point) => ({
      month: formatChartMonth(point.month),
      score: point.score,
    })),
    recentRegistrations: dto.recent_registrations.map((user) => ({
      userId: user.user_id,
      name: user.name,
      email: user.email,
      time: formatDateTime(user.created_at),
    })),
  };
}

export function mapAdminUser(dto: AdminUserDto): ManagedUser {
  return {
    id: dto.user_id,
    name: dto.name,
    email: dto.email,
    sessions: dto.session_count,
    joinedAt: formatDateTime(dto.created_at),
    role: dto.role === 'admin' ? 'admin' : 'user',
    disabled: !dto.is_active,
  };
}
