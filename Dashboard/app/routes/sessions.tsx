import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router';
import { PageLayout } from '../components/PageLayout';
import { ProtectedRoute } from '../components/ProtectedRoute';
import { getSessions } from '../services/sessionService';
import { SessionTable } from '../components/SessionTable';
import { SectionHeader } from '../components/SectionHeader';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import type { SessionListItem } from '../types/session';
import { getApiErrorMessage } from '../utils/apiError';
import { EmptyState } from '../components/EmptyState';
import { History } from 'lucide-react';

export default function Sessions() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<SessionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSessions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getSessions();
      setSessions(data);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to load sessions.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchSessions();
  }, [fetchSessions]);

  return (
    <ProtectedRoute allowedRoles={['user']}>
      <PageLayout>
        <SectionHeader
          title="Session Management"
          subtitle={`Track your progress and review detailed performance analytics from ${sessions.length} recorded VR sessions.`}
        />

        {loading && <LoadingSpinner text="Loading sessions..." />}
        {error && <ErrorMessage message={error} onRetry={fetchSessions} />}

        {!loading && !error && sessions.length === 0 && (
          <EmptyState
            icon={History}
            title="No sessions found"
            description="Your completed and processing VR training sessions will appear here after you start training."
          />
        )}

        {!loading && !error && sessions.length > 0 && (
          <SessionTable
            sessions={sessions}
            actionLabel="View Analysis"
            onRowClick={(id) => navigate(`/session-analytics/${id}`)}
            onRefresh={fetchSessions}
          />
        )}
      </PageLayout>
    </ProtectedRoute>
  );
}
