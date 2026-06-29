import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router";
import { PageLayout } from "../components/PageLayout";
import { ProtectedRoute } from "../components/ProtectedRoute";
import { getAnalyticsSessions } from "../services/analyticsService";
import { SessionTable } from "../components/SessionTable";
import { SectionHeader } from "../components/SectionHeader";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { ErrorMessage } from "../components/ErrorMessage";
import type { SessionListItem } from "../types/session";
import { getApiErrorMessage } from "../utils/apiError";
import { EmptyState } from "../components/EmptyState";
import { ChartNoAxesCombined } from "lucide-react";

export default function Analytics() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<SessionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSessions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getAnalyticsSessions();
      setSessions(data);
    } catch (err) {
      setError(getApiErrorMessage(err, "Failed to load analytics data."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchSessions();
  }, [fetchSessions]);

  return (
    <ProtectedRoute allowedRoles={["user"]}>
      <PageLayout>
        <SectionHeader
          title="Performance Analytics"
          subtitle={`Select a session to review its detailed AI performance analysis. ${sessions.length} sessions available.`}
        />

        {loading && <LoadingSpinner text="Loading analytics..." />}
        {error && <ErrorMessage message={error} onRetry={fetchSessions} />}

        {!loading && !error && sessions.length === 0 && (
          <EmptyState
            icon={ChartNoAxesCombined}
            title="No analytics available"
            description="Complete a VR training session first. Its voice, motion, and performance analysis will then appear here."
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
