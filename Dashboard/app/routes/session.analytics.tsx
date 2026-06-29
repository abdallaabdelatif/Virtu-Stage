import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router';
import { PageLayout } from '../components/PageLayout';
import { ProtectedRoute } from '../components/ProtectedRoute';
import {
  ArrowLeft,
  CheckCircle,
  AlertTriangle,
  Loader2,
} from 'lucide-react';
import { getSessionAnalytics } from '../services/analyticsService';
import { styles } from '../utils/styles';
import { SectionHeader } from '../components/SectionHeader';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { AnalyticsStatCard } from '../components/AnalyticsStatCard';
import { FeedbackItem } from '../components/FeedbackItem';
import { RecommendationItem } from '../components/RecommendationItem';
import { StatusBadge } from '../components/StatusBadge';
import type { SessionAnalytics as SessionAnalyticsData } from '../types/analytics';
import { getApiErrorMessage } from '../utils/apiError';
import { pct } from '../mappers/sessionReportMapper';
import { useSessionPolling } from '../hooks/useSessionPolling';
import type { BackendSessionStatus } from '../types/session';

function ProcessingBanner({ label }: { label: string }) {
  return (
    <div className="mb-6 rounded-2xl border border-[#FFB703]/30 bg-[#FFB703]/10 px-5 py-4 flex items-center gap-3 text-[#FFB703]">
      <Loader2 className="w-5 h-5 animate-spin" />
      <p className="text-sm font-semibold">{label}</p>
    </div>
  );
}

function FailedBanner({ label }: { label: string }) {
  return (
    <div className="mb-6 rounded-2xl border border-red-500/30 bg-red-500/10 px-5 py-4 text-red-300 text-sm font-semibold">
      {label}
    </div>
  );
}

export default function SessionAnalytics() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState<SessionAnalyticsData | null>(null);
  const [backendStatus, setBackendStatus] = useState<BackendSessionStatus | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSessionAnalytics = useCallback(async () => {
    if (!id) {
      setError('Session ID is missing from the URL.');
      setLoading(false);
      return;
    }

    try {
      setError(null);
      const sessionData = await getSessionAnalytics(id);
      setSession(sessionData);
      setBackendStatus(sessionData.backendStatus);
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, 'Failed to load session analytics.'));
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void fetchSessionAnalytics();
  }, [fetchSessionAnalytics]);

  useSessionPolling(
    id ?? null,
    backendStatus,
    fetchSessionAnalytics,
  );

  if (loading) {
    return (
      <ProtectedRoute allowedRoles={['user']}>
        <PageLayout>
          <LoadingSpinner text="Analyzing session data..." />
        </PageLayout>
      </ProtectedRoute>
    );
  }

  if (error || !session) {
    return (
      <ProtectedRoute allowedRoles={['user']}>
        <PageLayout>
          <ErrorMessage
            title="Analysis Unavailable"
            message={error || 'Analytics not found for this session'}
            onRetry={
              id && error !== 'Analytics not found for this session'
                ? fetchSessionAnalytics
                : undefined
            }
          />
        </PageLayout>
      </ProtectedRoute>
    );
  }

  const showVoice = !session.voicePending && !session.voiceFailed;
  const showMotion = !session.motionPending && !session.motionFailed;

  return (
    <ProtectedRoute allowedRoles={['user']}>
      <PageLayout>
        <button
          onClick={() => navigate('/analytics')}
          className="flex items-center gap-2 text-[#9aa1bc] hover:text-white text-sm font-medium mb-4 transition-colors group"
        >
          <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
          Back to Sessions
        </button>

        <SectionHeader
          title={session.title}
          subtitle={`${session.scenario} • ${session.difficulty} • ${session.date} • ${session.time} (${session.duration})`}
        />

        <div className="flex items-center gap-3 mb-6 -mt-4">
          <StatusBadge status={session.status} />
          <span className="text-[#5c6484] text-xs uppercase tracking-wider font-bold">
            Report: {session.reportStatus}
          </span>
        </div>

        {session.voicePending && (
          <ProcessingBanner label="Voice analysis is still processing." />
        )}
        {session.motionPending && (
          <ProcessingBanner label="Motion analysis is still processing." />
        )}
        {session.voiceFailed && (
          <FailedBanner label="Voice analysis failed or timed out. Motion results are shown when available." />
        )}
        {session.motionFailed && (
          <FailedBanner label="Motion analysis failed or timed out. Voice results are shown when available." />
        )}

        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          <AnalyticsStatCard
            label="Overall Score"
            value={session.overallScore ?? 'N/A'}
            barProgress={session.overallScore ?? 0}
          />
          <AnalyticsStatCard
            label="Voice Score"
            value={session.voiceScore ?? 'N/A'}
            barProgress={session.voiceScore ?? 0}
          />
          <AnalyticsStatCard
            label="Motion Score"
            value={session.motionScore ?? 'N/A'}
            barProgress={session.motionScore ?? 0}
          />
        </div>

        <div className="mb-8">
          <h2 className={`${styles.heading2} mb-4`}>Voice Delivery</h2>
          {showVoice ? (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <AnalyticsStatCard
                label="Speech Rate (WPM)"
                value={session.speechRate ?? 'N/A'}
                subText="Target range: 115-165"
              />
              <AnalyticsStatCard
                label="Filler Words"
                value={session.fillerWords ?? 'N/A'}
                subText="Um, ah, like, so"
              />
              <AnalyticsStatCard
                label="Pause Ratio"
                value={pct(session.pauseRatio)}
                subText={
                  session.pauseCount != null
                    ? `${session.pauseCount} pauses`
                    : undefined
                }
              />
              <AnalyticsStatCard
                label="Longest Pause"
                value={
                  session.longestPauseSeconds != null
                    ? `${session.longestPauseSeconds.toFixed(1)}s`
                    : 'N/A'
                }
              />
              <AnalyticsStatCard label="Confidence" value={pct(session.confidence)} />
              <AnalyticsStatCard label="Clarity" value={pct(session.clarity)} />
              <AnalyticsStatCard label="Focus" value={pct(session.focus)} />
              <AnalyticsStatCard label="Anxiety" value={pct(session.anxiety)} />
              <AnalyticsStatCard
                label="Voice Quality"
                value={pct(session.voiceQualityScore)}
                badgeText={session.voiceQualityLevel ?? undefined}
                badgeType="neutral"
              />
              <AnalyticsStatCard
                label="Fluency"
                value={pct(session.fluencyScore)}
                badgeText={session.fluencyLevel ?? undefined}
                badgeType="neutral"
              />
              <AnalyticsStatCard
                label="Energy Control"
                value={pct(session.energyControlScore)}
                badgeText={session.energyControlLevel ?? undefined}
                badgeType="neutral"
              />
              <AnalyticsStatCard
                label="Articulation"
                value={pct(session.articulationScore)}
                badgeText={session.articulationLevel ?? undefined}
                badgeType="neutral"
              />
            </div>
          ) : (
            <p className={styles.textMuted}>
              Voice metrics will appear when analysis is ready.
            </p>
          )}
        </div>

        {showVoice && session.voiceFeedback.length > 0 && (
          <div className="mb-8">
            <h2 className={`${styles.heading2} mb-4`}>Voice Feedback</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {session.voiceFeedback.map((item, index) => (
                <RecommendationItem
                  key={item.title}
                  num={index + 1}
                  title={item.title}
                  desc={item.desc}
                />
              ))}
            </div>
          </div>
        )}

        <div className="mb-8">
          <h2 className={`${styles.heading2} mb-4`}>Motion Delivery</h2>
          {showMotion ? (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <AnalyticsStatCard
                label="Posture"
                value={session.postureScore ?? 'N/A'}
              />
              <AnalyticsStatCard
                label="Gaze Assessment"
                value={session.gazeAssessment ?? 'N/A'}
              />
              <AnalyticsStatCard
                label="Gestures"
                value={session.gesturesScore ?? 'N/A'}
              />
              <AnalyticsStatCard
                label="Composure"
                value={session.composureAssessment ?? 'N/A'}
              />
              <AnalyticsStatCard
                label="Stability"
                value={
                  session.stabilityScore != null
                    ? pct(session.stabilityScore)
                    : 'N/A'
                }
              />
              <AnalyticsStatCard
                label="Fidgeting"
                value={session.fidgetingLevel ?? 'N/A'}
              />
              <AnalyticsStatCard
                label="Nervousness"
                value={session.nervousness ?? 'N/A'}
              />
            </div>
          ) : (
            <p className={styles.textMuted}>
              Motion metrics will appear when analysis is ready.
            </p>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="space-y-5">
            <div>
              <h3 className={styles.heading3}>
                <CheckCircle className="w-5 h-5 text-[#0bda62]" /> Key Strengths
              </h3>
              <div className="space-y-2">
                {session.strengths.length > 0 ? (
                  session.strengths.map((s) => (
                    <FeedbackItem
                      key={s.title}
                      title={s.title}
                      desc={s.desc}
                      type="strength"
                    />
                  ))
                ) : (
                  <p className={styles.textMuted}>No strengths identified yet.</p>
                )}
              </div>
            </div>
            <div>
              <h3 className={styles.heading3}>
                <AlertTriangle className="w-5 h-5 text-orange-400" /> Growth Areas
              </h3>
              <div className="space-y-2">
                {session.growthAreas.length > 0 ? (
                  session.growthAreas.map((g) => (
                    <FeedbackItem
                      key={g.title}
                      title={g.title}
                      desc={g.desc}
                      type="growth"
                    />
                  ))
                ) : (
                  <p className={styles.textMuted}>No growth areas identified yet.</p>
                )}
              </div>
            </div>
          </div>

          <div className="lg:col-span-2 bg-[#1e2433] rounded-3xl p-7 border border-transparent">
            <div className={`${styles.flexBetween} mb-6`}>
              <div>
                <h3 className="text-white text-2xl font-black">
                  Motion Recommendations
                </h3>
                <p className={styles.cardSubtitle}>
                  Based on motion analysis for this session
                </p>
              </div>
            </div>
            <div className="space-y-5">
              {session.recommendations.length > 0 ? (
                session.recommendations.map((r, i) => (
                  <RecommendationItem
                    key={i}
                    num={i + 1}
                    title={r.title}
                    desc={r.desc}
                  />
                ))
              ) : (
                <p className={styles.textMuted}>
                  Recommendations will appear when motion analysis is ready.
                </p>
              )}
            </div>
          </div>
        </div>
      </PageLayout>
    </ProtectedRoute>
  );
}
