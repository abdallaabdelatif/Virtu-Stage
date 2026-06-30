import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router';
import { getSessions } from '../services/sessionService';
import { SessionTable } from '../components/SessionTable';
import { SectionHeader } from '../components/SectionHeader';
import { ErrorMessage } from '../components/ErrorMessage';
import type { SessionListItem } from '../types/session';
import { getApiErrorMessage } from '../utils/apiError';
import { EmptyState } from '../components/EmptyState';
import { History } from 'lucide-react';
import { SessionListSkeleton } from '../components/PageSkeletons';
import { useTransientMessages } from '../hooks/useTransientMessages';
import { RefreshNotice } from '../components/RefreshNotice';

let cachedSessions: SessionListItem[] | null = null;

export default function Sessions() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<SessionListItem[]>(
    () => cachedSessions ?? [],
  );
  const [loading, setLoading] = useState(() => cachedSessions === null);
  const [error, setError] = useState<string | null>(null);
  const { messages: refreshMessages, appendMessage: appendRefreshMessage } =
    useTransientMessages();
  const mountedRef = useRef(false);

  const fetchSessions = useCallback(async () => {
    const hasCachedSnapshot = cachedSessions !== null;
    try {
      if (!hasCachedSnapshot) setLoading(true);
      setError(null);
      const data = await getSessions();
      if (!mountedRef.current) return;
      cachedSessions = data;
      setSessions(data);
    } catch (err) {
      if (!mountedRef.current) return;
      const message = getApiErrorMessage(err, 'Failed to load sessions.');
      if (cachedSessions !== null) {
        appendRefreshMessage(`${message} Showing the latest sessions.`);
      } else {
        setError(message);
      }
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }, [appendRefreshMessage]);

  useEffect(() => {
    mountedRef.current = true;
    void fetchSessions();
    return () => {
      mountedRef.current = false;
    };
  }, [fetchSessions]);

  return (
    <>
      <SectionHeader
        title="Session Management"
        subtitle={
          loading
            ? 'Track your progress and review detailed performance analytics.'
            : `Track your progress and review detailed performance analytics from ${sessions.length} recorded VR sessions.`
        }
      />

      <RefreshNotice messages={refreshMessages} />

      {loading && sessions.length === 0 && <SessionListSkeleton />}
      {error && <ErrorMessage message={error} onRetry={fetchSessions} />}

      {!error && !loading && sessions.length === 0 && (
        <EmptyState
          icon={History}
          title="No VR sessions yet"
          description="Complete a VR training session and your performance analytics will appear here."
        />
      )}

      {!error && sessions.length > 0 && (
        <SessionTable
          sessions={sessions}
          actionLabel="View Analysis"
          onRowClick={(id) => navigate(`/session-analytics/${id}`)}
          onRefresh={fetchSessions}
        />
      )}
    </>
  );
}
