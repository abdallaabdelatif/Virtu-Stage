import { useEffect, useState } from 'react';
import { API_ENDPOINTS } from '../config/api';
import { mapSessionStatus } from '../mappers/sessionMapper';
import type {
  BackendSessionStatus,
  SessionStatus,
  SessionStatusResponseDto,
} from '../types/session';
import { isNonTerminalStatus } from '../types/session';
import api from '../utils/api';

const TERMINAL_STATUSES: SessionStatus[] = ['Completed', 'Failed', 'Cancelled'];
// Central marks analysis as timed out after 10 minutes. Keep a small grace
// period, but never let a broken deployment or repeated network errors poll
// forever in a browser tab.
export const MAX_SESSION_POLLING_MS = 11 * 60 * 1000;

export function useSessionPolling(
  sessionId: string | null,
  backendStatus: BackendSessionStatus | null,
  onTerminal?: () => void,
) {
  const shouldPoll = Boolean(
    sessionId && backendStatus && isNonTerminalStatus(backendStatus),
  );
  const [status, setStatus] = useState<SessionStatus>(
    backendStatus ? mapSessionStatus(backendStatus) : 'Pending',
  );
  const [isPolling, setIsPolling] = useState(shouldPoll);

  useEffect(() => {
    if (!backendStatus) return;
    const mapped = mapSessionStatus(backendStatus);
    setStatus(mapped);
    setIsPolling(isNonTerminalStatus(backendStatus));
  }, [sessionId, backendStatus]);

  useEffect(() => {
    if (!sessionId || !isPolling) return;

    let active = true;
    let timer: number | undefined;
    const pollingStartedAt = Date.now();
    const poll = async () => {
      if (Date.now() - pollingStartedAt >= MAX_SESSION_POLLING_MS) {
        if (active) {
          setStatus('Failed');
          setIsPolling(false);
          onTerminal?.();
        }
        return;
      }

      let reachedTerminal = false;
      try {
        const { data } = await api.get<SessionStatusResponseDto>(
          API_ENDPOINTS.sessions.status(sessionId),
        );
        if (!active) return;
        // Both stored callbacks are enough to consider the analysis complete,
        // even while an older backend deployment still reports `processing`.
        const nextStatus =
          data.voice_ready && data.motion_ready
            ? 'Completed'
            : mapSessionStatus(data.status);
        setStatus(nextStatus);
        if (TERMINAL_STATUSES.includes(nextStatus)) {
          reachedTerminal = true;
          setIsPolling(false);
          onTerminal?.();
        }
      } catch {
        // Retry temporary failures on the next interval.
      } finally {
        if (active && !reachedTerminal) {
          timer = window.setTimeout(poll, 3000);
        }
      }
    };

    void poll();
    return () => {
      active = false;
      if (timer !== undefined) window.clearTimeout(timer);
    };
  }, [sessionId, isPolling, onTerminal]);

  return { isPolling, status };
}
