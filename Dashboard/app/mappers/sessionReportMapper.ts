import type { SessionAnalytics, FeedbackItem } from '../types/analytics';
import type { SessionReportDto, VoiceAnalysisDto } from '../types/report.dto';
import {
  formatPlatformDate,
  formatPlatformTime,
  parseApiDateTime,
  platformTimestampMs,
} from '../utils/dateTime';
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

interface RankedFeedback extends FeedbackItem {
  priority: number;
}

interface VoiceFeedbackParts {
  desc: string;
  reasons: string[];
}

function normalizedScore(value: number | null | undefined): number | null {
  if (value == null || !Number.isFinite(value)) return null;
  return value >= 0 && value <= 1 ? value * 100 : value;
}

function feedbackFor(
  feedback: Record<string, VoiceFeedbackParts>,
  key: string,
  fallback: string,
): Pick<FeedbackItem, 'desc' | 'reasons'> {
  const item = feedback[key];
  const desc = item?.desc.trim() || fallback;
  return item?.reasons.length ? { desc, reasons: item.reasons } : { desc };
}

function cleanReasons(reasons: string[] | null | undefined): string[] {
  return (reasons ?? [])
    .map((reason) => reason.trim())
    .filter((reason) => reason.length > 0);
}

function buildVoiceInsights(voice: VoiceAnalysisDto | null): {
  strengths: RankedFeedback[];
  growthAreas: RankedFeedback[];
  recommendations: RankedFeedback[];
} {
  if (!voice) return { strengths: [], growthAreas: [], recommendations: [] };

  const strengths: RankedFeedback[] = [];
  const growthAreas: RankedFeedback[] = [];
  const recommendations: RankedFeedback[] = [];
  const feedback = {
    confidence: {
      desc: voice.confidence_feedback,
      reasons: cleanReasons(voice.confidence_reasons),
    },
    clarity: {
      desc: voice.clarity_feedback,
      reasons: cleanReasons(voice.clarity_reasons),
    },
    focus: {
      desc: voice.focus_feedback,
      reasons: cleanReasons(voice.focus_reasons),
    },
    anxiety: {
      desc: voice.anxiety_feedback,
      reasons: cleanReasons(voice.anxiety_reasons),
    },
  };

  const positiveTraits = [
    ['Confidence', voice.confidence_level, 'confidence'],
    ['Clarity', voice.clarity_level, 'clarity'],
    ['Focus', voice.focus_level, 'focus'],
  ] as const;

  for (const [title, rawScore, key] of positiveTraits) {
    const score = normalizedScore(rawScore);
    if (score == null) continue;
    if (score >= 80) {
      strengths.push({
        title: `Voice: ${title}`,
        ...feedbackFor(
          feedback,
          key,
          `${title} was a strong part of this delivery.`,
        ),
        priority: score,
      });
    } else if (score < 60) {
      const feedbackItem = feedbackFor(
        feedback,
        key,
        `${title} needs more consistency.`,
      );
      growthAreas.push({
        title: `Voice: ${title}`,
        ...feedbackItem,
        priority: 100 - score,
      });
      recommendations.push({
        title: `Improve ${title.toLowerCase()}`,
        ...feedbackItem,
        priority: 100 - score,
      });
    }
  }

  const anxiety = normalizedScore(voice.anxiety_level);
  if (anxiety != null) {
    if (anxiety <= 25) {
      strengths.push({
        title: 'Voice: Composure',
        ...feedbackFor(
          feedback,
          'anxiety',
          'Your voice showed few signs of anxiety.',
        ),
        priority: 100 - anxiety,
      });
    } else if (anxiety >= 50) {
      const feedbackItem = feedbackFor(
        feedback,
        'anxiety',
        'Your voice showed elevated anxiety signals.',
      );
      growthAreas.push({
        title: 'Voice: Composure',
        ...feedbackItem,
        priority: anxiety,
      });
      recommendations.push({
        title: 'Reset before key answers',
        ...feedbackItem,
        priority: anxiety,
      });
    }
  }

  const deliveryScores = [
    ['Voice Quality', voice.voice_quality_score, voice.voice_quality_level],
    ['Fluency', voice.fluency_score, voice.fluency_level],
    ['Energy Control', voice.energy_control_score, voice.energy_control_level],
    ['Articulation', voice.articulation_score, voice.articulation_level],
  ] as const;

  for (const [title, rawScore, level] of deliveryScores) {
    const score = normalizedScore(rawScore);
    if (score == null) continue;
    const levelText = formatRating(level) ?? 'measured';
    if (score >= 80) {
      strengths.push({
        title: `Voice: ${title}`,
        desc: `${title} was ${levelText.toLowerCase()} at ${Math.round(score)}%.`,
        priority: score,
      });
    } else if (score < 60) {
      const desc = `${title} was ${levelText.toLowerCase()} at ${Math.round(score)}%.`;
      growthAreas.push({
        title: `Voice: ${title}`,
        desc,
        priority: 100 - score,
      });
      recommendations.push({
        title: `Practice ${title.toLowerCase()}`,
        desc,
        priority: 100 - score,
      });
    }
  }

  const wpm = voice.words_per_minute;
  if (wpm != null && (wpm < 115 || wpm > 165)) {
    const direction = wpm < 115 ? 'slow' : 'fast';
    const priority = Math.min(
      100,
      Math.abs(wpm - (wpm < 115 ? 115 : 165)) + 45,
    );
    const desc = `Your pace was ${Math.round(wpm)} WPM, which is ${direction} compared with the 115-165 target range.`;
    growthAreas.push({ title: 'Voice: Speaking pace', desc, priority });
    recommendations.push({
      title: `Use a ${direction === 'slow' ? 'quicker' : 'steadier'} pace`,
      desc,
      priority,
    });
  }

  if (voice.pause_ratio != null && voice.pause_ratio > 0.2) {
    const desc = `${pct(voice.pause_ratio)} of the session was paused; shorter, intentional pauses will improve flow.`;
    growthAreas.push({
      title: 'Voice: Pause control',
      desc,
      priority: voice.pause_ratio * 100,
    });
    recommendations.push({
      title: 'Make pauses intentional',
      desc,
      priority: voice.pause_ratio * 100,
    });
  }

  return { strengths, growthAreas, recommendations };
}

function uniqueRanked(
  items: RankedFeedback[],
  limit: number,
  maxPerSource = limit,
): FeedbackItem[] {
  const seen = new Set<string>();
  const sourceCounts = new Map<string, number>();
  return items
    .sort((a, b) => b.priority - a.priority)
    .filter((item) => {
      if (seen.has(item.title)) return false;
      const source = item.title.split(':', 1)[0];
      const sourceCount = sourceCounts.get(source) ?? 0;
      if (sourceCount >= maxPerSource) return false;
      seen.add(item.title);
      sourceCounts.set(source, sourceCount + 1);
      return true;
    })
    .slice(0, limit)
    .map(({ title, desc }) => ({ title, desc }));
}

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
    const label = key
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase());
    const detail = dimensionDetail(assessment, key);

    if (rating && goodRatings.includes(rating)) {
      strengths.push({
        title: label,
        desc: detail || `${label} rated ${rating}.`,
      });
    } else if (rating && weakRatings.includes(rating)) {
      growthAreas.push({
        title: label,
        desc: detail || `${label} rated ${rating}.`,
      });
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

  const voiceInsights = buildVoiceInsights(voice);
  const motionStrengths: RankedFeedback[] = strengths.map((item) => ({
    ...item,
    title: `Motion: ${item.title}`,
    priority: 75,
  }));
  const motionGrowthAreas: RankedFeedback[] = growthAreas.map((item) => ({
    ...item,
    title: `Motion: ${item.title}`,
    priority: 75,
  }));

  const motionRecommendations: RankedFeedback[] = (
    motion?.recommendations ?? []
  ).map((text, index) => ({
    title: `Motion practice ${index + 1}`,
    desc: text,
    priority: 70 - index,
  }));

  const voiceFeedback: FeedbackItem[] = voice
    ? [
        {
          title: 'Confidence',
          desc: voice.confidence_feedback,
          reasons: cleanReasons(voice.confidence_reasons),
        },
        {
          title: 'Clarity',
          desc: voice.clarity_feedback,
          reasons: cleanReasons(voice.clarity_reasons),
        },
        {
          title: 'Focus',
          desc: voice.focus_feedback,
          reasons: cleanReasons(voice.focus_reasons),
        },
        {
          title: 'Anxiety',
          desc: voice.anxiety_feedback,
          reasons: cleanReasons(voice.anxiety_reasons),
        },
      ]
        .filter((item) => item.desc.trim().length > 0)
        .map((item) =>
          item.reasons.length > 0
            ? item
            : { title: item.title, desc: item.desc },
        )
    : [];

  const startValue = session.start_time ?? session.created_at;
  const startDate = startValue ? parseApiDateTime(startValue) : null;
  const combinedStrengths = uniqueRanked(
    [...voiceInsights.strengths, ...motionStrengths],
    3,
    2,
  );
  const combinedGrowthAreas = uniqueRanked(
    [...voiceInsights.growthAreas, ...motionGrowthAreas],
    3,
    2,
  );
  const combinedRecommendations = uniqueRanked(
    [...voiceInsights.recommendations, ...motionRecommendations],
    3,
  );
  const overallScore = normalizedScore(session.overall_score);
  const reportSummary =
    combinedGrowthAreas.length > 0
      ? `A ${overallScore != null ? `${Math.round(overallScore)}/100 ` : ''}session with ${combinedStrengths.length > 0 ? 'clear strengths' : 'useful baseline data'} and ${combinedGrowthAreas.length} priority ${combinedGrowthAreas.length === 1 ? 'area' : 'areas'} to improve next.`
      : `A ${overallScore != null ? `${Math.round(overallScore)}/100 ` : ''}session with balanced delivery and no major weaknesses detected.`;

  return {
    id: session.session_id ?? fallbackId,
    title: `${mapScenario(session.scenario_type)} Session`,
    date: startDate ? formatPlatformDate(startValue) : 'N/A',
    time: startDate ? formatPlatformTime(startValue) : 'N/A',
    duration:
      session.start_time && session.end_time
        ? `${Math.max(
            0,
            Math.round(
              (platformTimestampMs(session.end_time) -
                platformTimestampMs(session.start_time)) /
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
    reportSummary,
    postureScore: motion?.posture_score ?? null,
    gazeAssessment: assessment
      ? formatRating(ratingLabel(assessment.gaze))
      : null,
    gesturesScore: motion?.hand_movement_score ?? null,
    composureAssessment: assessment
      ? formatRating(ratingLabel(assessment.composure))
      : null,
    stabilityScore: motion?.head_stability_score ?? null,
    fidgetingLevel: formatRating(motion?.fidgeting_level ?? null),
    fidgetingScore: motion?.fidgeting_score ?? null,
    dominantPostureType: formatRating(motion?.dominant_posture_type ?? null),
    nervousness: motion?.nervousness_indicator ?? null,
    strengths: combinedStrengths,
    growthAreas: combinedGrowthAreas,
    recommendations: combinedRecommendations,
    voicePending: dto.voice_status === 'pending',
    motionPending: dto.motion_status === 'pending',
    voiceFailed: dto.voice_status === 'failed',
    motionFailed: dto.motion_status === 'failed',
  };
}

export { pct };
