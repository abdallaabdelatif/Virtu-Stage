import { StatCard } from './Card';
import { SectionHeader } from './SectionHeader';
import { BarChart2, Star, Zap, Sparkles } from 'lucide-react';
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
  Legend,
} from 'recharts';
import type { UserDashboardData } from '../types/dashboard';
import { formatImprovementRate } from '../types/dashboard';
import { EmptyState } from './EmptyState';

interface UserDashboardProps {
  name: string;
  data: UserDashboardData;
}

export function UserDashboard({ name, data }: UserDashboardProps) {
  const {
    progressData,
    voiceMotionData,
    totalSessions,
    analyzedSessions,
    avgScore,
    improvementRate,
  } = data;

  const improvementLabel = formatImprovementRate(improvementRate);

  return (
    <>
      <SectionHeader
        title={`Welcome back, ${name?.split(' ')[0]} 👋`}
        subtitle={
          totalSessions === 0
            ? 'Complete your first VR session to begin tracking your progress.'
            : `You have ${totalSessions} recorded session${totalSessions === 1 ? '' : 's'} with ${analyzedSessions} analyzed.`
        }
      />

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <StatCard
          label="Total Sessions"
          value={totalSessions.toString()}
          change={
            totalSessions === 0
              ? 'Complete your first training session'
              : 'Your recorded training sessions'
          }
          color="#5c7cff"
          icon={<BarChart2 className="w-5 h-5" />}
        />
        <StatCard
          label="Avg Performance Score"
          value={avgScore != null ? `${avgScore}/100` : '--'}
          change={
            analyzedSessions === 0
              ? 'Available after your first completed analysis'
              : 'Based on completed analyzed sessions'
          }
          color="#FFB703"
          icon={<Star className="w-5 h-5" />}
        />
        <StatCard
          label="Improvement Rate"
          value={improvementLabel}
          change={
            improvementRate == null
              ? 'Requires at least 10 completed sessions'
              : 'Recent 5 sessions vs the previous 5'
          }
          color="#0bda62"
          icon={<Zap className="w-5 h-5" />}
        />
      </div>

      {totalSessions === 0 ? (
        <EmptyState
          icon={Sparkles}
          title="No sessions yet"
          description="Start your first VR training session to unlock performance scores, progress trends, and voice and motion analytics."
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className={styles.card}>
            <div className="mb-4">
              <h2 className={styles.cardTitle}>Performance Progress</h2>
              <p className={styles.cardSubtitle}>
                Overall score from completed sessions
              </p>
              <div className="flex items-baseline gap-2 mt-2">
                <span className="text-white text-3xl font-black">
                  {avgScore ?? '--'}
                </span>
                {improvementRate != null ? (
                  <span
                    className={`text-sm font-bold ${
                      improvementRate >= 0 ? 'text-[#0bda62]' : 'text-red-400'
                    }`}
                  >
                    {improvementLabel}
                  </span>
                ) : null}
              </div>
            </div>
            {progressData.length === 0 ? (
              <p className={styles.textMuted}>
                Score history appears after sessions are completed and scored.
              </p>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={[...progressData].reverse()}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#272b3a" />
                  <XAxis
                    dataKey="date"
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
                    stroke="#5c7cff"
                    strokeWidth={3}
                    dot={false}
                    activeDot={{ r: 6, fill: '#5c7cff' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className={styles.card}>
            <div className="mb-4">
              <h2 className={styles.cardTitle}>Voice vs. Motion Analytics</h2>
              <p className={styles.cardSubtitle}>
                Recent completed sessions by component score
              </p>
            </div>
            {voiceMotionData.length === 0 ? (
              <p className={styles.textMuted}>
                Voice and motion scores appear after sessions finish analysis.
              </p>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={voiceMotionData} barGap={4}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#272b3a" />
                  <XAxis
                    dataKey="label"
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
                  <Legend
                    formatter={(value) => (
                      <span style={{ color: '#9aa1bc' }}>{value}</span>
                    )}
                  />
                  <Bar
                    dataKey="voice"
                    name="Voice"
                    fill="#5c7cff"
                    radius={[4, 4, 0, 0]}
                  />
                  <Bar
                    dataKey="motion"
                    name="Motion"
                    fill="#3d4f8a"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      )}
    </>
  );
}
