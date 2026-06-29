import type { BackendSessionStatus } from './session';

export interface FeedbackItem {
  title: string;
  desc: string;
}

export interface MetricCard {
  label: string;
  value: string | number;
  subText?: string;
}

export interface SessionAnalytics {
  id: string;
  title: string;
  date: string;
  time: string;
  duration: string;
  scenario: string;
  difficulty: string;
  status: string;
  backendStatus: BackendSessionStatus;
  reportStatus: string;
  voiceStatus: string;
  motionStatus: string;
  overallScore: number | null;
  voiceScore: number | null;
  motionScore: number | null;
  speechRate: number | null;
  fillerWords: number | null;
  pauseRatio: number | null;
  pauseCount: number | null;
  longestPauseSeconds: number | null;
  confidence: number | null;
  clarity: number | null;
  focus: number | null;
  anxiety: number | null;
  voiceQualityScore: number | null;
  voiceQualityLevel: string | null;
  fluencyScore: number | null;
  fluencyLevel: string | null;
  energyControlScore: number | null;
  energyControlLevel: string | null;
  articulationScore: number | null;
  articulationLevel: string | null;
  voiceFeedback: FeedbackItem[];
  postureScore: number | null;
  gazeAssessment: string | null;
  gesturesScore: number | null;
  composureAssessment: string | null;
  stabilityScore: number | null;
  fidgetingLevel: string | null;
  nervousness: number | null;
  strengths: FeedbackItem[];
  growthAreas: FeedbackItem[];
  recommendations: FeedbackItem[];
  voicePending: boolean;
  motionPending: boolean;
  voiceFailed: boolean;
  motionFailed: boolean;
}
