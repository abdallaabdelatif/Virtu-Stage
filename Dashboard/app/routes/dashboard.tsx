import {
  lazy,
  Suspense,
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react';
import { useAuth } from '../context/AuthContext';
import { getDashboardStats } from '../services/dashboardService';
import { ErrorMessage } from '../components/ErrorMessage';
import { getApiErrorMessage } from '../utils/apiError';
import type { AdminDashboardData, UserDashboardData } from '../types/dashboard';
import { DashboardSkeleton } from '../components/PageSkeletons';
import { useTransientMessages } from '../hooks/useTransientMessages';
import { RefreshNotice } from '../components/RefreshNotice';

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

type DashboardRole = 'admin' | 'user';
type DashboardStats = AdminDashboardData | UserDashboardData;

const cachedDashboardStats = new Map<string, DashboardStats>();

export default function Dashboard() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';
  const roleKey: DashboardRole = isAdmin ? 'admin' : 'user';
  const cacheKey = user ? `${roleKey}:${user.id}` : null;
  const cachedStats = cacheKey ? cachedDashboardStats.get(cacheKey) : null;

  const [loading, setLoading] = useState(() => cachedStats == null);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(
    () => cachedStats ?? null,
  );
  const { messages: refreshMessages, appendMessage: appendRefreshMessage } =
    useTransientMessages();
  const mountedRef = useRef(false);

  const fetchDashboardData = useCallback(async () => {
    if (!cacheKey) return;
    const hasCachedSnapshot = cachedDashboardStats.has(cacheKey);
    try {
      if (!hasCachedSnapshot) setLoading(true);
      setError(null);
      const data = isAdmin
        ? await getDashboardStats('admin')
        : await getDashboardStats('user');
      if (!mountedRef.current) return;
      cachedDashboardStats.set(cacheKey, data);
      setStats(data);
    } catch (err: unknown) {
      if (!mountedRef.current) return;
      const message = getApiErrorMessage(err, 'Failed to load dashboard data.');
      if (cachedDashboardStats.has(cacheKey)) {
        appendRefreshMessage(`${message} Showing the latest dashboard data.`);
      } else {
        setError(message);
      }
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }, [appendRefreshMessage, cacheKey, isAdmin]);

  useEffect(() => {
    mountedRef.current = true;
    const nextCachedStats = cacheKey
      ? cachedDashboardStats.get(cacheKey)
      : undefined;
    if (nextCachedStats) {
      setStats(nextCachedStats);
      setLoading(false);
      setError(null);
    } else {
      setStats(null);
      setLoading(true);
    }
    if (user) {
      fetchDashboardData();
    }
    return () => {
      mountedRef.current = false;
    };
  }, [cacheKey, fetchDashboardData, user]);

  if (loading && !stats) {
    return <DashboardSkeleton />;
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
    <>
      <RefreshNotice messages={refreshMessages} />
      <Suspense fallback={<DashboardSkeleton />}>
        {'totalUsers' in stats ? (
          <AdminDashboard name={user?.name ?? ''} data={stats} />
        ) : (
          <UserDashboard name={user?.name ?? ''} data={stats} />
        )}
      </Suspense>
    </>
  );
}
