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
import { formatPlatformDate, formatPlatformTime } from '../utils/dateTime';

interface UserDashboardProps {
  name: string;
  data: UserDashboardData;
}

function formatTooltipTimestamp(value: string) {
  const date = formatPlatformDate(value, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
  const time = formatPlatformTime(value, {
    hour: 'numeric',
    minute: '2-digit',
  });
  return `${date}, ${time}`;
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
  const orderedProgressData = [...progressData].reverse();
  const progressLabels = new Map(
    progressData.map((point) => [point.sessionId, point.date]),
  );
  const progressTooltipLabels = new Map(
    progressData.map((point) => [
      point.sessionId,
      formatTooltipTimestamp(point.timestamp),
    ]),
  );
  const voiceMotionLabels = new Map(
    voiceMotionData.map((point) => [point.sessionId, point.label]),
  );
  const voiceMotionTooltipLabels = new Map(
    voiceMotionData.map((point) => [
      point.sessionId,
      formatTooltipTimestamp(point.timestamp),
    ]),
  );

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
          description={
            totalSessions === 0
              ? 'Complete your first training session'
              : 'Your recorded training sessions'
          }
          color="#c1ff72"
          icon={<BarChart2 className="w-5 h-5" />}
        />
        <StatCard
          label="Avg Performance Score"
          value={avgScore != null ? `${avgScore}/100` : '--'}
          description={
            analyzedSessions === 0
              ? 'Available after your first completed analysis'
              : 'Based on completed analyzed sessions'
          }
          progress={avgScore ?? undefined}
          color="#FFB703"
          icon={<Star className="w-5 h-5" />}
        />
        <StatCard
          label="Improvement Rate"
          value={improvementLabel}
          description={
            improvementRate == null
              ? 'Requires at least 10 completed sessions'
              : 'Recent 5 sessions vs the previous 5'
          }
          valueTone={
            improvementRate == null || improvementRate === 0
              ? 'neutral'
              : improvementRate > 0
                ? 'positive'
                : 'negative'
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
                <LineChart data={orderedProgressData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a3325" />
                  <XAxis
                    dataKey="sessionId"
                    tickFormatter={(sessionId) =>
                      progressLabels.get(String(sessionId)) ?? ''
                    }
                    tick={{ fill: '#aeb4a8', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: '#aeb4a8', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    domain={[0, 100]}
                  />
                  <Tooltip
                    content={
                      <CustomTooltip
                        labelFormatter={(sessionId) =>
                          progressTooltipLabels.get(String(sessionId)) ?? ''
                        }
                      />
                    }
                  />
                  <Line
                    type="monotone"
                    dataKey="score"
                    stroke="#c1ff72"
                    strokeWidth={3}
                    dot={
                      orderedProgressData.length === 1
                        ? { r: 5, fill: '#c1ff72' }
                        : false
                    }
                    activeDot={{ r: 6, fill: '#c1ff72' }}
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
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a3325" />
                  <XAxis
                    dataKey="sessionId"
                    tickFormatter={(sessionId) =>
                      voiceMotionLabels.get(String(sessionId)) ?? ''
                    }
                    tick={{ fill: '#aeb4a8', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: '#aeb4a8', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    domain={[0, 100]}
                  />
                  <Tooltip
                    content={
                      <CustomTooltip
                        labelFormatter={(sessionId) =>
                          voiceMotionTooltipLabels.get(String(sessionId)) ?? ''
                        }
                      />
                    }
                  />
                  <Legend
                    formatter={(value) => (
                      <span style={{ color: '#d9d9d9' }}>{value}</span>
                    )}
                  />
                  <Bar
                    dataKey="voice"
                    name="Voice"
                    fill="#c1ff72"
                    radius={[4, 4, 0, 0]}
                  />
                  <Bar
                    dataKey="motion"
                    name="Motion"
                    fill="#d9d9d9"
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
