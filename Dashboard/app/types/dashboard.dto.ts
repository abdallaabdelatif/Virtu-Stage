export interface UserDashboardDto {
  total_sessions: number;
  analyzed_sessions: number;
  average_overall_score: number | null;
  improvement_rate: number | null;
  score_history: Array<{
    session_id: string;
    date: string;
    score: number;
  }>;
  analysis_history: Array<{
    session_id: string;
    label: string;
    voice_score: number;
    motion_score: number;
  }>;
}

export interface AdminDashboardDto {
  total_users: number;
  total_sessions: number;
  platform_average_score: number | null;
  sessions_today: number;
  sessions_by_day: Array<{ date: string; count: number }>;
  average_score_by_month: Array<{ month: string; score: number }>;
  recent_registrations: Array<{
    user_id: string;
    name: string;
    email: string;
    created_at: string;
  }>;
}

export interface AdminUserDto {
  user_id: string;
  name: string;
  email: string;
  role: string;
  is_active: boolean;
  session_count: number;
  created_at: string;
}
