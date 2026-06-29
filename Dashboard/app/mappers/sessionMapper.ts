import type {
  BackendSessionDto,
  BackendSessionStatus,
  SessionDetail,
  SessionListItem,
  SessionStatus,
} from '../types/session';

export function mapSessionStatus(status: BackendSessionStatus): SessionStatus {
  const statuses: Record<BackendSessionStatus, SessionStatus> = {
    pending: 'Pending',
    in_progress: 'In Progress',
    processing: 'Processing Analysis',
    completed: 'Completed',
    failed: 'Failed',
    cancelled: 'Cancelled',
  };
  return statuses[status];
}

export function mapScenario(scenario: BackendSessionDto['scenario_type']) {
  return scenario === 'interview' ? 'Job Interview' : 'Public Speaking';
}

function formatDate(value: string | null) {
  if (!value) return { date: 'Not started', time: '' };
  const date = new Date(value);
  return {
    date: date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    }),
    time: date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    }),
  };
}

function formatDuration(start: string | null, end: string | null) {
  if (!start || !end) return 'N/A';
  const seconds = Math.max(
    0,
    Math.floor((new Date(end).getTime() - new Date(start).getTime()) / 1000),
  );
  const minutes = Math.floor(seconds / 60);
  return `${minutes}:${String(seconds % 60).padStart(2, '0')}`;
}

export function mapBackendSession(dto: BackendSessionDto): SessionListItem {
  const { date, time } = formatDate(dto.start_time ?? dto.created_at);
  return {
    id: dto.session_id,
    date,
    time,
    scenario: mapScenario(dto.scenario_type),
    score: dto.overall_score,
    status: mapSessionStatus(dto.status),
    backendStatus: dto.status,
  };
}

export function mapBackendSessionDetail(dto: BackendSessionDto): SessionDetail {
  return {
    ...mapBackendSession(dto),
    title: `${mapScenario(dto.scenario_type)} Session`,
    duration: formatDuration(dto.start_time, dto.end_time),
    difficulty: dto.difficulty_level,
  };
}
