import { lazy, Suspense, useCallback, useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { getDashboardStats } from '../services/dashboardService';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { getApiErrorMessage } from '../utils/apiError';
import type { AdminDashboardData, UserDashboardData } from '../types/dashboard';

const UserDashboard = lazy(() =>
  import('../components/UserDashboard').then((module) => ({
    default: module.UserDashboard,
  })),
);
const AdminDashboard = lazy(() =>
  import('../components/AdminDashboard').then((module) => ({
    default: module.AdminDashboard,
  })),
);

export default function Dashboard() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<
    AdminDashboardData | UserDashboardData | null
  >(null);

  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = isAdmin
        ? await getDashboardStats('admin')
        : await getDashboardStats('user');
      setStats(data);
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, 'Failed to load dashboard data.'));
    } finally {
      setLoading(false);
    }
  }, [isAdmin]);

  useEffect(() => {
    if (user) {
      fetchDashboardData();
    }
  }, [fetchDashboardData, user]);

  if (loading) {
    return <LoadingSpinner text="Loading your dashboard..." />;
  }

  if (error || !stats) {
    return (
      <ErrorMessage
        title="Dashboard Unavailable"
        message={error || 'No data found'}
        onRetry={fetchDashboardData}
      />
    );
  }

  return (
    <Suspense
      fallback={<LoadingSpinner text="Preparing dashboard charts..." />}
    >
      {'totalUsers' in stats ? (
        <AdminDashboard name={user?.name ?? ''} data={stats} />
      ) : (
        <UserDashboard name={user?.name ?? ''} data={stats} />
      )}
    </Suspense>
  );
}
