export interface PerformancePoint {
  date: string;
  score: number;
}

export interface VoiceMotionPoint {
  label: string;
  voice: number;
  motion: number;
}

export interface UserDashboardData {
  totalSessions: number;
  analyzedSessions: number;
  avgScore: number | null;
  improvementRate: number | null;
  progressData: PerformancePoint[];
  voiceMotionData: VoiceMotionPoint[];
}

export interface AdminSessionsPoint {
  day: string;
  sessions: number;
}

export interface AdminScorePoint {
  month: string;
  score: number;
}

export interface RecentRegistration {
  userId: string;
  name: string;
  email: string;
  time: string;
}

export interface AdminDashboardData {
  totalUsers: number;
  totalSessions: number;
  platformAvgScore: number | null;
  sessionsToday: number;
  adminSessionsData: AdminSessionsPoint[];
  adminScoreData: AdminScorePoint[];
  recentRegistrations: RecentRegistration[];
}

export function formatImprovementRate(value: number | null): string {
  if (value == null) return '--';
  const prefix = value > 0 ? '+' : '';
  return `${prefix}${value}%`;
}
