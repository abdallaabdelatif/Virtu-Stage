import { useState, useEffect, useCallback, type ReactNode } from 'react';
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
    return { label: 'Unavailable', className: 'text-[#9aa1bc] bg-white/5' };
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
    <div className="rounded-2xl border border-[#393f56] bg-[#1b1d28] p-5">
      <div className="flex items-start justify-between gap-3">
        <p className={styles.labelMuted}>{label}</p>
        <span
          className={`rounded-full px-2.5 py-1 text-[11px] font-bold ${tone.className}`}
        >
          {tone.label}
        </span>
      </div>
      <p className="mt-3 text-2xl font-black text-white">{value}</p>
      <p className="mt-2 text-sm leading-relaxed text-[#9aa1bc]">{detail}</p>
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
    <details className="group rounded-2xl border border-[#393f56] bg-[#1b1d28]">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-4 p-5">
        <div>
          <p className="font-bold text-white">{title}</p>
          <p className="mt-1 text-sm text-[#9aa1bc]">{subtitle}</p>
        </div>
        <ChevronDown className="h-5 w-5 text-[#9aa1bc] transition-transform group-open:rotate-180" />
      </summary>
      <div className="border-t border-[#393f56] p-5">{children}</div>
    </details>
  );
}

export default function SessionAnalytics() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState<SessionAnalyticsData | null>(null);
  const [backendStatus, setBackendStatus] =
    useState<BackendSessionStatus | null>(null);
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

  useSessionPolling(id ?? null, backendStatus, fetchSessionAnalytics);

  if (loading) {
    return <LoadingSpinner text="Analyzing session data..." />;
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
    ...(session.speechRate != null
      ? [
          {
            label: 'Speaking pace',
            value: `${Math.round(session.speechRate)} WPM`,
            detail: 'A natural conversational target is 115-165 WPM.',
            score:
              session.speechRate >= 115 && session.speechRate <= 165 ? 90 : 45,
          },
        ]
      : []),
    ...(session.fluencyScore != null
      ? [
          {
            label: 'Fluency',
            value: pct(session.fluencyScore),
            detail: `${session.fillerWords ?? 0} fillers and ${session.pauseCount ?? 0} detected pauses.`,
            score: scoreValue(session.fluencyScore),
          },
        ]
      : []),
    ...(session.energyControlScore != null
      ? [
          {
            label: 'Vocal control',
            value: pct(session.energyControlScore),
            detail:
              'How consistently your loudness and emphasis were controlled.',
            score: scoreValue(session.energyControlScore),
          },
        ]
      : []),
    ...(session.articulationScore != null
      ? [
          {
            label: 'Expression',
            value: pct(session.articulationScore),
            detail: 'Articulation and clarity of vocal expression.',
            score: scoreValue(session.articulationScore),
          },
        ]
      : []),
    ...(session.voiceQualityScore != null
      ? [
          {
            label: 'Voice quality',
            value: pct(session.voiceQualityScore),
            detail: 'Stability and cleanliness of the recorded voice.',
            score: scoreValue(session.voiceQualityScore),
          },
        ]
      : []),
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
            label: 'Anxiety evidence',
            value: pct(session.anxiety),
            detail:
              voiceFeedbackByTitle.get('Anxiety') ??
              'Lower evidence indicates a calmer vocal delivery.',
            score: scoreValue(session.anxiety),
            inverse: true,
          },
        ]
      : []),
  ].slice(0, 4);

  return (
    <>
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
        <span className="text-[#858dab] text-xs uppercase tracking-wider font-bold">
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
          <div className="rounded-2xl bg-brand p-3 text-white">
            <Sparkles className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-[#8da2ff]">
              Session summary
            </p>
            <p className="mt-2 max-w-4xl text-lg font-semibold leading-relaxed text-white">
              {session.reportSummary}
            </p>
          </div>
        </div>
      </section>

      <section className="mb-10 grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div className="rounded-3xl border border-[#0bda62]/15 bg-[#1b1d28] p-5">
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
                  type="strength"
                />
              ))
            ) : (
              <p className={styles.textMuted}>
                More evidence is needed to identify strengths.
              </p>
            )}
          </div>
        </div>

        <div className="rounded-3xl border border-orange-400/15 bg-[#1b1d28] p-5">
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
                  type="growth"
                />
              ))
            ) : (
              <p className={styles.textMuted}>
                No major weaknesses were detected.
              </p>
            )}
          </div>
        </div>

        <div className="rounded-3xl border border-[#393f56] bg-[#1e2433] p-5">
          <h3 className={styles.heading3}>
            <Sparkles className="h-5 w-5 text-[#8da2ff]" /> Next session plan
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
              <p className={styles.textMuted}>
                Keep practicing this balanced delivery.
              </p>
            )}
          </div>
        </div>
      </section>

      <section className="mb-10">
        <div className="mb-4 flex items-center gap-3">
          <Mic2 className="h-6 w-6 text-[#8da2ff]" />
          <div>
            <h2 className="text-2xl font-black text-white">Voice snapshot</h2>
            <p className="text-sm text-[#9aa1bc]">
              The four signals that best explain your delivery.
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
            <Mic2 className="h-6 w-6 text-[#8da2ff]" />
            <div>
              <h2 className="text-2xl font-black text-white">
                Voice analysis feedback
              </h2>
              <p className="text-sm text-[#9aa1bc]">
                Explanations generated from this session's vocal signals.
              </p>
            </div>
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {session.voiceFeedback.map((item) => (
              <div
                key={item.title}
                className="rounded-2xl border border-[#393f56] bg-[#1b1d28] p-5"
              >
                <p className="font-bold text-white">{item.title}</p>
                <p className="mt-2 text-sm leading-relaxed text-[#9aa1bc]">
                  {item.desc}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="mb-10">
        <div className="mb-4 flex items-center gap-3">
          <Move3d className="h-6 w-6 text-[#8da2ff]" />
          <div>
            <h2 className="text-2xl font-black text-white">Motion snapshot</h2>
            <p className="text-sm text-[#9aa1bc]">
              The visual signals with the greatest coaching value.
            </p>
          </div>
        </div>
        {showMotion ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <DeliverySnapshotCard
              label="Posture"
              value={
                session.postureScore != null
                  ? `${Math.round(session.postureScore)}/100`
                  : 'Unavailable'
              }
              detail="Upright, balanced positioning throughout the session."
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
            subtitle="Traits, timing, pauses, and acoustic delivery scores"
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
              {session.confidence != null && (
                <AnalyticsStatCard
                  label="Confidence"
                  value={pct(session.confidence)}
                />
              )}
              {session.clarity != null && (
                <AnalyticsStatCard
                  label="Clarity"
                  value={pct(session.clarity)}
                />
              )}
              {session.focus != null && (
                <AnalyticsStatCard label="Focus" value={pct(session.focus)} />
              )}
              {session.anxiety != null && (
                <AnalyticsStatCard
                  label="Anxiety Evidence"
                  value={pct(session.anxiety)}
                  subText="Lower is better"
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
            subtitle="Posture, gaze, movement, stability, and nervousness signals"
          >
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {session.postureScore != null && (
                <AnalyticsStatCard
                  label="Posture"
                  value={session.postureScore}
                />
              )}
              {session.gazeAssessment != null && (
                <AnalyticsStatCard
                  label="Gaze Assessment"
                  value={session.gazeAssessment}
                />
              )}
              {session.gesturesScore != null && (
                <AnalyticsStatCard
                  label="Gestures"
                  value={session.gesturesScore}
                />
              )}
              {session.composureAssessment != null && (
                <AnalyticsStatCard
                  label="Composure"
                  value={session.composureAssessment}
                />
              )}
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
