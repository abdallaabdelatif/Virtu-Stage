import { StatCard } from './Card';
import { SectionHeader } from './SectionHeader';
import {
  Users,
  Activity,
  TrendingUp,
  CalendarDays,
  ChartNoAxesCombined,
  UserRoundPlus,
} from 'lucide-react';
import { styles } from '../utils/styles';
import { CustomTooltip } from './CustomTooltip';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { AdminDashboardData } from '../types/dashboard';
import { EmptyState } from './EmptyState';

interface AdminDashboardProps {
  name: string;
  data: AdminDashboardData;
}

export function AdminDashboard({ name, data }: AdminDashboardProps) {
  const {
    adminSessionsData,
    adminScoreData,
    recentRegistrations,
    totalUsers,
    totalSessions,
    platformAvgScore,
    sessionsToday,
  } = data;

  return (
    <>
      <SectionHeader
        title={`Welcome back, ${name?.split(' ')[0]} 👋`}
        subtitle="Here's what's happening across the VirtuStage platform today."
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          label="Total Users"
          value={totalUsers.toString()}
          change={
            totalUsers === 0
              ? 'No registered users yet'
              : 'Registered platform users'
          }
          color="#5c7cff"
          icon={<Users className="w-5 h-5" />}
        />
        <StatCard
          label="Total Sessions"
          value={totalSessions.toString()}
          change={
            totalSessions === 0
              ? 'No sessions recorded yet'
              : 'Sessions across all users'
          }
          color="#0bda62"
          icon={<Activity className="w-5 h-5" />}
        />
        <StatCard
          label="Platform Avg Score"
          value={platformAvgScore != null ? `${platformAvgScore}/100` : '--'}
          change={
            totalSessions === 0
              ? 'Available after session analysis'
              : 'Average across completed sessions'
          }
          color="#FFB703"
          icon={<TrendingUp className="w-5 h-5" />}
        />
        <StatCard
          label="Sessions Today"
          value={sessionsToday.toString()}
          change={
            sessionsToday === 0
              ? 'No sessions started today'
              : 'Sessions created today (UTC)'
          }
          color="#f472b6"
          icon={<CalendarDays className="w-5 h-5" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className={styles.card}>
          <div className="mb-4">
            <h2 className={styles.cardTitle}>Session Activity</h2>
            <p className={styles.cardSubtitle}>
              Daily session count across all users
            </p>
          </div>
          {adminSessionsData.length === 0 ? (
            <EmptyState
              compact
              icon={ChartNoAxesCombined}
              title="No session activity yet"
              description="Platform session totals will appear after users begin training."
            />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={adminSessionsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#272b3a" />
                <XAxis
                  dataKey="day"
                  tick={{ fill: '#5c6484', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#5c6484', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar
                  dataKey="sessions"
                  name="Sessions"
                  fill="#5c7cff"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className={styles.card}>
          <div className="mb-4">
            <h2 className={styles.cardTitle}>Platform Average Score</h2>
            <p className={styles.cardSubtitle}>
              Monthly average across completed sessions
            </p>
          </div>
          {adminScoreData.length === 0 ? (
            <EmptyState
              compact
              icon={ChartNoAxesCombined}
              title="No score data yet"
              description="Platform averages will appear after analyzed sessions are available."
            />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={adminScoreData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#272b3a" />
                <XAxis
                  dataKey="month"
                  tick={{ fill: '#5c6484', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#5c6484', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  domain={[0, 100]}
                />
                <Tooltip content={<CustomTooltip />} />
                <Line
                  type="monotone"
                  dataKey="score"
                  name="Avg Score"
                  stroke="#0bda62"
                  strokeWidth={3}
                  dot={{ fill: '#0bda62', r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className={styles.card}>
        <div className={`${styles.flexBetween} mb-5`}>
          <h2 className={styles.cardTitle}>Recent Registrations</h2>
          <a href="/admin" className={styles.btnLink}>
            View All Users →
          </a>
        </div>
        {recentRegistrations.length === 0 ? (
          <EmptyState
            compact
            icon={UserRoundPlus}
            title="No recent registrations"
            description="Newly registered users will appear here."
          />
        ) : (
          <div className="space-y-3">
            {recentRegistrations.map((user) => (
              <div
                key={user.userId}
                className="flex flex-wrap items-center gap-4 p-3 rounded-xl bg-[#12141c] border border-[#272b3a]"
              >
                <div
                  className={`w-9 h-9 rounded-full bg-[#5c7cff]/20 ${styles.flexCenter} text-[#5c7cff] font-bold text-sm flex-shrink-0`}
                >
                  {user.name.charAt(0)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-white font-semibold text-sm">{user.name}</p>
                  <p className={styles.textMuted}>{user.email}</p>
                </div>
                <span className={styles.textMuted}>{user.time}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
