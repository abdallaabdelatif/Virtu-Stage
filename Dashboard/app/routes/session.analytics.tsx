import {
  useState,
  useEffect,
  useCallback,
  useRef,
  type ReactNode,
} from 'react';
import { useParams, useNavigate } from 'react-router';
import {
  ArrowLeft,
  CheckCircle,
  AlertTriangle,
  Loader2,
  ChevronDown,
  Mic2,
  Move3d,
  Sparkles,
} from 'lucide-react';
import { getSessionAnalytics } from '../services/analyticsService';
import { styles } from '../utils/styles';
import { SectionHeader } from '../components/SectionHeader';
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
import { SessionAnalyticsSkeleton } from '../components/PageSkeletons';
import { useTransientMessages } from '../hooks/useTransientMessages';
import { RefreshNotice } from '../components/RefreshNotice';

const cachedSessionAnalytics = new Map<string, SessionAnalyticsData>();

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

function scoreValue(value: number | null): number | null {
  if (value == null || !Number.isFinite(value)) return null;
  return value >= 0 && value <= 1 ? value * 100 : value;
}

function ratingScore(value: string | null): number | null {
  if (!value) return null;
  const rating = value.toLowerCase().replace(/\s+/g, '_');
  if (rating === 'excellent') return 90;
  if (rating === 'good') return 75;
  if (rating === 'developing' || rating === 'medium') return 50;
  if (rating === 'needs_work' || rating === 'high') return 25;
  if (rating === 'low') return 85;
  return null;
}

function deliveryTone(
  score: number | null,
  inverse = false,
): {
  label: string;
  className: string;
} {
  if (score == null)
    return { label: 'Unavailable', className: 'text-[#d9d9d9] bg-white/5' };
  const effective = inverse ? 100 - score : score;
  if (effective >= 80)
    return { label: 'Strong', className: 'text-[#0bda62] bg-[#0bda62]/10' };
  if (effective >= 60)
    return { label: 'Balanced', className: 'text-brand-soft bg-brand/10' };
  if (effective >= 40)
    return { label: 'Watch', className: 'text-[#FFB703] bg-[#FFB703]/10' };
  return {
    label: 'Needs attention',
    className: 'text-orange-400 bg-orange-400/10',
  };
}

function DeliverySnapshotCard({
  label,
  value,
  detail,
  score,
  inverse = false,
}: {
  label: string;
  value: string;
  detail: string;
  score: number | null;
  inverse?: boolean;
}) {
  const tone = deliveryTone(score, inverse);
  return (
    <div className="rounded-2xl border border-[#46513c] bg-[#1a2117] p-5">
      <div className="flex items-start justify-between gap-3">
        <p className={styles.labelMuted}>{label}</p>
        <span
          className={`rounded-full px-2.5 py-1 text-[11px] font-bold ${tone.className}`}
        >
          {tone.label}
        </span>
      </div>
      <p className="mt-3 text-2xl font-black text-white">{value}</p>
      <p className="mt-2 text-sm leading-relaxed text-[#d9d9d9]">{detail}</p>
    </div>
  );
}

interface VoiceSnapshotMetric {
  label: string;
  value: string;
  detail: string;
  score: number | null;
  inverse?: boolean;
}

function DetailSection({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <details className="group rounded-2xl border border-[#46513c] bg-[#1a2117]">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-4 p-5">
        <div>
          <p className="font-bold text-white">{title}</p>
          <p className="mt-1 text-sm text-[#d9d9d9]">{subtitle}</p>
        </div>
        <ChevronDown className="h-5 w-5 text-[#d9d9d9] transition-transform group-open:rotate-180" />
      </summary>
      <div className="border-t border-[#46513c] p-5">{children}</div>
    </details>
  );
}

export default function SessionAnalytics() {
  const { id } = useParams();
  const navigate = useNavigate();
  const cachedSession = id ? cachedSessionAnalytics.get(id) : null;
  const [session, setSession] = useState<SessionAnalyticsData | null>(
    () => cachedSession ?? null,
  );
  const [backendStatus, setBackendStatus] =
    useState<BackendSessionStatus | null>(
      () => cachedSession?.backendStatus ?? null,
    );
  const [loading, setLoading] = useState(() => !cachedSession);
  const [error, setError] = useState<string | null>(null);
  const { messages: refreshMessages, appendMessage: appendRefreshMessage } =
    useTransientMessages();
  const mountedRef = useRef(false);

  const fetchSessionAnalytics = useCallback(async () => {
    if (!id) {
      setError('Session ID is missing from the URL.');
      setLoading(false);
      return;
    }

    const hasCachedSnapshot = cachedSessionAnalytics.has(id);
    try {
      if (!hasCachedSnapshot) setLoading(true);
      setError(null);
      const sessionData = await getSessionAnalytics(id);
      if (!mountedRef.current) return;
      cachedSessionAnalytics.set(id, sessionData);
      setSession(sessionData);
      setBackendStatus(sessionData.backendStatus);
    } catch (err: unknown) {
      if (!mountedRef.current) return;
      const message = getApiErrorMessage(
        err,
        'Failed to load session analytics.',
      );
      if (cachedSessionAnalytics.has(id)) {
        appendRefreshMessage(`${message} Showing the latest analysis data.`);
      } else {
        setError(message);
      }
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }, [appendRefreshMessage, id]);

  useEffect(() => {
    mountedRef.current = true;
    if (id) {
      const cached = cachedSessionAnalytics.get(id);
      if (cached) {
        setSession(cached);
        setBackendStatus(cached.backendStatus);
        setLoading(false);
        setError(null);
      }
    }
    void fetchSessionAnalytics();
    return () => {
      mountedRef.current = false;
    };
  }, [fetchSessionAnalytics, id]);

  useSessionPolling(id ?? null, backendStatus, fetchSessionAnalytics);

  if (loading) {
    return <SessionAnalyticsSkeleton />;
  }

  if (error || !session) {
    return (
      <ErrorMessage
        title="Analysis Unavailable"
        message={error || 'Analytics not found for this session'}
        onRetry={
          id && error !== 'Analytics not found for this session'
            ? fetchSessionAnalytics
            : undefined
        }
      />
    );
  }

  const showVoice = !session.voicePending && !session.voiceFailed;
  const showMotion = !session.motionPending && !session.motionFailed;
  const voiceFeedbackByTitle = new Map(
    session.voiceFeedback.map((item) => [item.title, item.desc]),
  );
  const voiceSnapshotMetrics: VoiceSnapshotMetric[] = [
    ...(session.confidence != null
      ? [
          {
            label: 'Confidence',
            value: pct(session.confidence),
            detail:
              voiceFeedbackByTitle.get('Confidence') ??
              'How assured and steady the delivery sounded.',
            score: scoreValue(session.confidence),
          },
        ]
      : []),
    ...(session.clarity != null
      ? [
          {
            label: 'Clarity',
            value: pct(session.clarity),
            detail:
              voiceFeedbackByTitle.get('Clarity') ??
              'How clearly the message could be understood.',
            score: scoreValue(session.clarity),
          },
        ]
      : []),
    ...(session.focus != null
      ? [
          {
            label: 'Focus',
            value: pct(session.focus),
            detail:
              voiceFeedbackByTitle.get('Focus') ??
              'How consistently the delivery stayed on track.',
            score: scoreValue(session.focus),
          },
        ]
      : []),
    ...(session.anxiety != null
      ? [
          {
            label: 'Anxiety',
            value: pct(session.anxiety),
            detail:
              voiceFeedbackByTitle.get('Anxiety') ??
              'Lower evidence indicates a calmer vocal delivery.',
            score: scoreValue(session.anxiety),
            inverse: true,
          },
        ]
      : []),
  ];

  return (
    <>
      <button
        onClick={() => navigate('/analytics')}
        className="flex items-center gap-2 text-[#d9d9d9] hover:text-white text-sm font-medium mb-4 transition-colors group"
      >
        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
        Back to Sessions
      </button>

      <SectionHeader
        title={session.title}
        subtitle={`${session.scenario} • ${session.difficulty} • ${session.date} • ${session.time} (${session.duration})`}
      />

      <RefreshNotice messages={refreshMessages} />

      <div className="flex items-center gap-3 mb-6 -mt-4">
        <StatusBadge status={session.status} />
        <span className="text-[#aeb4a8] text-xs uppercase tracking-wider font-bold">
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
          value={scoreValue(session.overallScore) ?? 'N/A'}
          barProgress={scoreValue(session.overallScore) ?? 0}
        />
        <AnalyticsStatCard
          label="Voice Score"
          value={scoreValue(session.voiceScore) ?? 'N/A'}
          barProgress={scoreValue(session.voiceScore) ?? 0}
        />
        <AnalyticsStatCard
          label="Motion Score"
          value={scoreValue(session.motionScore) ?? 'N/A'}
          barProgress={scoreValue(session.motionScore) ?? 0}
        />
      </div>

      <section className="mb-8 rounded-3xl border border-brand/30 bg-brand/10 p-6">
        <div className="flex items-start gap-4">
          <div className="rounded-2xl bg-brand p-3 text-brand-contrast">
            <Sparkles className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-[#c1ff72]">
              Session summary
            </p>
            <p className="mt-2 max-w-4xl text-lg font-semibold leading-relaxed text-white">
              {session.reportSummary}
            </p>
          </div>
        </div>
      </section>

      <section className="mb-10 grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div className="rounded-3xl border border-[#0bda62]/15 bg-[#1a2117] p-5">
          <h3 className={styles.heading3}>
            <CheckCircle className="h-5 w-5 text-[#0bda62]" /> Top strengths
          </h3>
          <div className="space-y-3">
            {session.strengths.length > 0 ? (
              session.strengths.map((item) => (
                <FeedbackItem
                  key={item.title}
                  title={item.title}
                  desc={item.desc}
                  reasons={item.reasons}
                  type="strength"
                />
              ))
            ) : (
              <p className={`${styles.textMuted} text-sm sm:text-base`}>
                More evidence is needed to identify strengths.
              </p>
            )}
          </div>
        </div>

        <div className="rounded-3xl border border-orange-400/15 bg-[#1a2117] p-5">
          <h3 className={styles.heading3}>
            <AlertTriangle className="h-5 w-5 text-orange-400" /> Priority
            improvements
          </h3>
          <div className="space-y-3">
            {session.growthAreas.length > 0 ? (
              session.growthAreas.map((item) => (
                <FeedbackItem
                  key={item.title}
                  title={item.title}
                  desc={item.desc}
                  reasons={item.reasons}
                  type="growth"
                />
              ))
            ) : (
              <p className={`${styles.textMuted} text-sm sm:text-base`}>
                No major weaknesses were detected.
              </p>
            )}
          </div>
        </div>

        <div className="rounded-3xl border border-[#46513c] bg-[#1e2433] p-5">
          <h3 className={styles.heading3}>
            <Sparkles className="h-5 w-5 text-[#c1ff72]" /> Next session plan
          </h3>
          <div className="space-y-5">
            {session.recommendations.length > 0 ? (
              session.recommendations.map((item, index) => (
                <RecommendationItem
                  key={item.title}
                  num={index + 1}
                  title={item.title}
                  desc={item.desc}
                />
              ))
            ) : (
              <p className={`${styles.textMuted} text-sm sm:text-base`}>
                Keep practicing this balanced delivery.
              </p>
            )}
          </div>
        </div>
      </section>

      <section className="mb-10">
        <div className="mb-4 flex items-center gap-3">
          <Mic2 className="h-6 w-6 text-[#c1ff72]" />
          <div>
            <h2 className="text-2xl font-black text-white">Voice snapshot</h2>
            <p className="text-sm text-[#d9d9d9]">
              The four primary outcomes used to evaluate your vocal delivery.
            </p>
          </div>
        </div>
        {showVoice ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {voiceSnapshotMetrics.map((metric) => (
              <DeliverySnapshotCard key={metric.label} {...metric} />
            ))}
          </div>
        ) : (
          <p className={styles.textMuted}>
            Voice metrics will appear when analysis is ready.
          </p>
        )}
      </section>

      {showVoice && session.voiceFeedback.length > 0 && (
        <section className="mb-10">
          <div className="mb-4 flex items-center gap-3">
            <Mic2 className="h-6 w-6 text-[#c1ff72]" />
            <div>
              <h2 className="text-2xl font-black text-white">
                Voice analysis feedback
              </h2>
              <p className="text-sm text-[#d9d9d9]">
                Feedback with supporting reasons from this session&apos;s vocal
                signals.
              </p>
            </div>
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {session.voiceFeedback.map((item) => (
              <div
                key={item.title}
                className="rounded-2xl border border-[#46513c] bg-[#1a2117] p-5"
              >
                <p className="text-xl font-black text-white">{item.title}</p>
                <p className="mt-2 text-sm leading-relaxed text-[#d9d9d9]">
                  {item.desc}
                </p>
                {item.reasons && item.reasons.length > 0 && (
                  <ul className="mt-3 space-y-2 text-base leading-relaxed text-[#b8c0b0]">
                    {item.reasons.map((reason) => (
                      <li key={reason} className="flex gap-2">
                        <span className="text-[#c1ff72]">•</span>
                        <span>{reason}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="mb-10">
        <div className="mb-4 flex items-center gap-3">
          <Move3d className="h-6 w-6 text-[#c1ff72]" />
          <div>
            <h2 className="text-2xl font-black text-white">Motion snapshot</h2>
            <p className="text-sm text-[#d9d9d9]">
              The visual signals with the greatest coaching value.
            </p>
          </div>
        </div>
        {showMotion ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <DeliverySnapshotCard
              label="Posture"
              value={
                session.dominantPostureType ??
                (session.postureScore != null
                  ? `${Math.round(session.postureScore)}/100`
                  : 'Unavailable')
              }
              detail={
                session.dominantPostureType && session.postureScore != null
                  ? `Most frequent posture, with a quality score of ${Math.round(session.postureScore)}/100.`
                  : session.dominantPostureType
                    ? 'The posture observed most often during the session.'
                    : 'Overall posture quality throughout the session.'
              }
              score={scoreValue(session.postureScore)}
            />
            <DeliverySnapshotCard
              label="Gaze"
              value={session.gazeAssessment ?? 'Unavailable'}
              detail="How consistently your attention stayed forward-facing."
              score={ratingScore(session.gazeAssessment)}
            />
            <DeliverySnapshotCard
              label="Gestures"
              value={
                session.gesturesScore != null
                  ? `${Math.round(session.gesturesScore)}/100`
                  : 'Unavailable'
              }
              detail="Purposeful hand movement that supports your message."
              score={scoreValue(session.gesturesScore)}
            />
            <DeliverySnapshotCard
              label="Composure"
              value={session.composureAssessment ?? 'Unavailable'}
              detail="Visible steadiness and control under pressure."
              score={ratingScore(session.composureAssessment)}
            />
          </div>
        ) : (
          <p className={styles.textMuted}>
            Motion metrics will appear when analysis is ready.
          </p>
        )}
      </section>

      <section className="mb-8 space-y-4">
        <h2 className="text-2xl font-black text-white">
          Detailed measurements
        </h2>
        {showVoice && (
          <DetailSection
            title="All voice measurements"
            subtitle="Supporting timing, pause, fluency, and acoustic measurements"
          >
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {session.speechRate != null && (
                <AnalyticsStatCard
                  label="Speech Rate (WPM)"
                  value={Math.round(session.speechRate)}
                  subText="Target: 115-165"
                />
              )}
              {session.fillerWords != null && (
                <AnalyticsStatCard
                  label="Filler Words"
                  value={session.fillerWords}
                />
              )}
              {session.pauseRatio != null && (
                <AnalyticsStatCard
                  label="Pause Ratio"
                  value={pct(session.pauseRatio)}
                  subText={
                    session.pauseCount != null
                      ? `${session.pauseCount} pauses`
                      : undefined
                  }
                />
              )}
              {session.longestPauseSeconds != null && (
                <AnalyticsStatCard
                  label="Longest Pause"
                  value={`${session.longestPauseSeconds.toFixed(1)}s`}
                />
              )}
              {session.voiceQualityScore != null && (
                <AnalyticsStatCard
                  label="Voice Quality"
                  value={pct(session.voiceQualityScore)}
                  badgeText={session.voiceQualityLevel ?? undefined}
                  badgeType="neutral"
                />
              )}
              {session.fluencyScore != null && (
                <AnalyticsStatCard
                  label="Fluency"
                  value={pct(session.fluencyScore)}
                  badgeText={session.fluencyLevel ?? undefined}
                  badgeType="neutral"
                />
              )}
              {session.energyControlScore != null && (
                <AnalyticsStatCard
                  label="Energy Control"
                  value={pct(session.energyControlScore)}
                  badgeText={session.energyControlLevel ?? undefined}
                  badgeType="neutral"
                />
              )}
              {session.articulationScore != null && (
                <AnalyticsStatCard
                  label="Articulation"
                  value={pct(session.articulationScore)}
                  badgeText={session.articulationLevel ?? undefined}
                  badgeType="neutral"
                />
              )}
            </div>
          </DetailSection>
        )}
        {showMotion && (
          <DetailSection
            title="All motion measurements"
            subtitle="Supporting stability, fidgeting, and nervousness signals"
          >
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {session.stabilityScore != null && (
                <AnalyticsStatCard
                  label="Stability"
                  value={pct(session.stabilityScore)}
                />
              )}
              {session.fidgetingLevel != null && (
                <AnalyticsStatCard
                  label="Fidgeting"
                  value={session.fidgetingLevel}
                  subText="Lower is better"
                />
              )}
              {session.fidgetingScore != null && (
                <AnalyticsStatCard
                  label="Fidgeting Score"
                  value={pct(session.fidgetingScore)}
                  subText="Lower is better"
                />
              )}
              {session.nervousness != null && (
                <AnalyticsStatCard
                  label="Nervousness Evidence"
                  value={session.nervousness}
                  subText="Lower is better"
                />
              )}
            </div>
          </DetailSection>
        )}
      </section>
    </>
  );
}
