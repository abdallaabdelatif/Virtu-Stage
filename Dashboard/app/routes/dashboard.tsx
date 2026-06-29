import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { PageLayout } from '../components/PageLayout';
import { ProtectedRoute } from '../components/ProtectedRoute';
import { getDashboardStats } from '../services/dashboardService';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { UserDashboard } from '../components/UserDashboard';
import { AdminDashboard } from '../components/AdminDashboard';
import { getApiErrorMessage } from '../utils/apiError';
import type {
  AdminDashboardData,
  UserDashboardData,
} from '../types/dashboard';

export default function Dashboard() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<
    AdminDashboardData | UserDashboardData | null
  >(null);

  const fetchDashboardData = async () => {
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
  };

  useEffect(() => {
    if (user) {
      fetchDashboardData();
    }
  }, [user]);

  if (loading) {
    return (
      <ProtectedRoute>
        <PageLayout>
          <LoadingSpinner text="Loading your dashboard..." />
        </PageLayout>
      </ProtectedRoute>
    );
  }

  if (error || !stats) {
    return (
      <ProtectedRoute>
        <PageLayout>
          <ErrorMessage
            title="Dashboard Unavailable"
            message={error || 'No data found'}
            onRetry={fetchDashboardData}
          />
        </PageLayout>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <PageLayout>
        {'totalUsers' in stats ? (
          <AdminDashboard
            name={user?.name ?? ''}
            data={stats}
          />
        ) : (
          <UserDashboard
            name={user?.name ?? ''}
            data={stats}
          />
        )}
      </PageLayout>
    </ProtectedRoute>
  );
}
