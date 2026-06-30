import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router';
import { getAnalyticsSessions } from '../services/analyticsService';
import { SessionTable } from '../components/SessionTable';
import { SectionHeader } from '../components/SectionHeader';
import { ErrorMessage } from '../components/ErrorMessage';
import type { SessionListItem } from '../types/session';
import { getApiErrorMessage } from '../utils/apiError';
import { EmptyState } from '../components/EmptyState';
import { ChartNoAxesCombined } from 'lucide-react';
import { SessionListSkeleton } from '../components/PageSkeletons';
import { useTransientMessages } from '../hooks/useTransientMessages';
import { RefreshNotice } from '../components/RefreshNotice';

let cachedAnalyticsSessions: SessionListItem[] | null = null;

export default function Analytics() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<SessionListItem[]>(
    () => cachedAnalyticsSessions ?? [],
  );
  const [loading, setLoading] = useState(
    () => cachedAnalyticsSessions === null,
  );
  const [error, setError] = useState<string | null>(null);
  const { messages: refreshMessages, appendMessage: appendRefreshMessage } =
    useTransientMessages();
  const mountedRef = useRef(false);

  const fetchSessions = useCallback(async () => {
    const hasCachedSnapshot = cachedAnalyticsSessions !== null;
    try {
      if (!hasCachedSnapshot) setLoading(true);
      setError(null);
      const data = await getAnalyticsSessions();
      if (!mountedRef.current) return;
      cachedAnalyticsSessions = data;
      setSessions(data);
    } catch (err) {
      if (!mountedRef.current) return;
      const message = getApiErrorMessage(err, 'Failed to load analytics data.');
      if (cachedAnalyticsSessions !== null) {
        appendRefreshMessage(`${message} Showing the latest analytics data.`);
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
        title="Performance Analytics"
        subtitle={
          loading
            ? 'Select a session to review its detailed AI performance analysis.'
            : `Select a session to review its detailed AI performance analysis. ${sessions.length} sessions available.`
        }
      />

      <RefreshNotice messages={refreshMessages} />

      {loading && sessions.length === 0 && <SessionListSkeleton />}
      {error && <ErrorMessage message={error} onRetry={fetchSessions} />}

      {!error && !loading && sessions.length === 0 && (
        <EmptyState
          icon={ChartNoAxesCombined}
          title="No analytics available"
          description="Complete a VR training session first. Its voice, motion, and performance analysis will then appear here."
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
