import type { SessionAnalytics, FeedbackItem } from '../types/analytics';
import type { SessionReportDto } from '../types/report.dto';
import { mapScenario, mapSessionStatus } from './sessionMapper';

function pct(value: number | null | undefined): string {
  if (value == null) return 'N/A';
  const normalized = value >= 0 && value <= 1 ? value * 100 : value;
  return `${Math.round(Math.min(100, Math.max(0, normalized)))}%`;
}

function ratingLabel(value: unknown): string | null {
  if (typeof value === 'string') return value;
  if (typeof value !== 'object' || value === null) return null;
  const rating = (value as { rating?: string }).rating;
  return rating ?? null;
}

const MOTION_DIMENSIONS = [
  'posture',
  'gaze',
  'gestures',
  'composure',
  'stability',
] as const;

function dimensionDetail(
  assessment: Record<string, unknown>,
  key: (typeof MOTION_DIMENSIONS)[number],
): string {
  const flatMeaning = assessment[`${key}_meaning`];
  if (typeof flatMeaning === 'string') return flatMeaning;

  const value = assessment[key];
  if (typeof value === 'object' && value !== null && 'detail' in value) {
    return String((value as { detail?: string }).detail ?? '');
  }
  return '';
}

function formatRating(value: string | null): string | null {
  if (!value) return null;
  return value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function buildDimensionFeedback(
  assessment: Record<string, unknown> | null | undefined,
  goodRatings: string[],
  weakRatings: string[],
): { strengths: FeedbackItem[]; growthAreas: FeedbackItem[] } {
  if (!assessment) return { strengths: [], growthAreas: [] };

  const strengths: FeedbackItem[] = [];
  const growthAreas: FeedbackItem[] = [];

  for (const key of MOTION_DIMENSIONS) {
    const value = assessment[key];
    const rating = ratingLabel(value);
    const label = key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
    const detail = dimensionDetail(assessment, key);

    if (rating && goodRatings.includes(rating)) {
      strengths.push({ title: label, desc: detail || `${label} rated ${rating}.` });
    } else if (rating && weakRatings.includes(rating)) {
      growthAreas.push({ title: label, desc: detail || `${label} rated ${rating}.` });
    }
  }

  return { strengths, growthAreas };
}

export function mapSessionReport(
  dto: SessionReportDto,
  fallbackId: string,
): SessionAnalytics {
  const session = dto.session;
  const voice = dto.voice_analysis;
  const motion = dto.motion_analysis;
  const assessment = motion?.presentation_assessment ?? null;

  const { strengths, growthAreas } = buildDimensionFeedback(
    assessment,
    ['excellent', 'good'],
    ['developing', 'needs_work'],
  );

  const recommendations: FeedbackItem[] = (motion?.recommendations ?? []).map(
    (text, index) => ({
      title: `Recommendation ${index + 1}`,
      desc: text,
    }),
  );

  const voiceFeedback: FeedbackItem[] = voice
    ? [
        { title: 'Confidence', desc: voice.confidence_feedback },
        { title: 'Clarity', desc: voice.clarity_feedback },
        { title: 'Focus', desc: voice.focus_feedback },
        { title: 'Anxiety', desc: voice.anxiety_feedback },
      ].filter((item) => item.desc.trim().length > 0)
    : [];

  const startValue = session.start_time ?? session.created_at;
  const startDate = startValue ? new Date(startValue) : null;

  return {
    id: session.session_id ?? fallbackId,
    title: `${mapScenario(session.scenario_type)} Session`,
    date: startDate
      ? startDate.toLocaleDateString()
      : 'N/A',
    time: startDate
      ? startDate.toLocaleTimeString()
      : 'N/A',
    duration:
      session.start_time && session.end_time
        ? `${Math.max(
            0,
            Math.round(
              (new Date(session.end_time).getTime() -
                new Date(session.start_time).getTime()) /
                60000,
            ),
          )} mins`
        : 'N/A',
    scenario: mapScenario(session.scenario_type),
    difficulty: session.difficulty_level,
    status: mapSessionStatus(session.status),
    backendStatus: session.status,
    reportStatus: dto.report_status,
    voiceStatus: dto.voice_status,
    motionStatus: dto.motion_status,
    overallScore: session.overall_score,
    voiceScore: session.voice_analysis_score ?? null,
    motionScore: session.motion_analysis_score ?? null,
    speechRate: voice?.words_per_minute ?? null,
    fillerWords: voice?.filler_word_count ?? null,
    pauseRatio: voice?.pause_ratio ?? null,
    pauseCount: voice?.pause_count ?? null,
    longestPauseSeconds: voice?.longest_pause_sec ?? null,
    confidence: voice?.confidence_level ?? null,
    clarity: voice?.clarity_level ?? null,
    focus: voice?.focus_level ?? null,
    anxiety: voice?.anxiety_level ?? null,
    voiceQualityScore: voice?.voice_quality_score ?? null,
    voiceQualityLevel: formatRating(voice?.voice_quality_level ?? null),
    fluencyScore: voice?.fluency_score ?? null,
    fluencyLevel: formatRating(voice?.fluency_level ?? null),
    energyControlScore: voice?.energy_control_score ?? null,
    energyControlLevel: formatRating(voice?.energy_control_level ?? null),
    articulationScore: voice?.articulation_score ?? null,
    articulationLevel: formatRating(voice?.articulation_level ?? null),
    voiceFeedback,
    postureScore: motion?.posture_score ?? null,
    gazeAssessment: assessment
      ? formatRating(ratingLabel(assessment.gaze))
      : null,
    gesturesScore: motion?.hand_movement_score ?? null,
    composureAssessment: assessment
      ? formatRating(ratingLabel(assessment.composure))
      : null,
    stabilityScore: motion?.head_stability_score ?? null,
    fidgetingLevel: motion?.fidgeting_level ?? null,
    nervousness: motion?.nervousness_indicator ?? null,
    strengths,
    growthAreas,
    recommendations,
    voicePending: dto.voice_status === 'pending',
    motionPending: dto.motion_status === 'pending',
    voiceFailed: dto.voice_status === 'failed',
    motionFailed: dto.motion_status === 'failed',
  };
}

export { pct };
