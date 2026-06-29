export type BackendSessionStatus =
  | 'pending'
  | 'in_progress'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'cancelled';

export type SessionStatus =
  | 'Pending'
  | 'In Progress'
  | 'Processing Analysis'
  | 'Completed'
  | 'Failed'
  | 'Cancelled';

export interface SessionStatusResponseDto {
  session_id: string;
  status: BackendSessionStatus;
  voice_ready: boolean;
  motion_ready: boolean;
}

export interface BackendSessionDto {
  session_id: string;
  user_id: string;
  scenario_type: 'interview' | 'public_speaking';
  difficulty_level: 'easy' | 'medium' | 'hard';
  status: BackendSessionStatus;
  start_time: string | null;
  end_time: string | null;
  overall_score: number | null;
  voice_analysis_score?: number | null;
  motion_analysis_score?: number | null;
  created_at: string;
}

export interface SessionListItem {
  id: string;
  date: string;
  time: string;
  scenario: string;
  score: number | null;
  status: SessionStatus;
  backendStatus: BackendSessionStatus;
}

export interface SessionDetail extends SessionListItem {
  title: string;
  duration: string;
  difficulty: string;
}

export function isNonTerminalStatus(status: BackendSessionStatus): boolean {
  return !['completed', 'failed', 'cancelled'].includes(status);
}
