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
    const poll = async () => {
      let reachedTerminal = false;
      try {
        const { data } = await api.get<SessionStatusResponseDto>(
          API_ENDPOINTS.sessions.status(sessionId),
        );
        if (!active) return;
        const nextStatus = mapSessionStatus(data.status);
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
