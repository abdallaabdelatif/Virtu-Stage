import type { BackendSessionDto } from './session';

export type ReportStatus = 'processing' | 'complete' | 'partial' | 'failed';
export type AnalysisComponentStatus = 'pending' | 'ready' | 'failed';

export interface VoiceAnalysisDto {
  confidence_level: number | null;
  anxiety_level: number | null;
  clarity_level: number | null;
  focus_level: number | null;
  voice_quality_score: number | null;
  voice_quality_level: string | null;
  fluency_score: number | null;
  fluency_level: string | null;
  energy_control_score: number | null;
  energy_control_level: string | null;
  articulation_score: number | null;
  articulation_level: string | null;
  words_per_minute: number | null;
  pause_ratio: number | null;
  filler_word_count: number | null;
  pause_count: number | null;
  longest_pause_sec: number | null;
  confidence_feedback: string;
  anxiety_feedback: string;
  clarity_feedback: string;
  focus_feedback: string;
  analyzed_at: string;
}

export interface MotionAnalysisDto {
  head_stability_score: number;
  fidgeting_level: string;
  fidgeting_score: number;
  hand_movement_score: number;
  posture_quality: number;
  posture_score: number;
  nervousness_indicator: number;
  motion_overall_score: number;
  presentation_assessment?: Record<string, unknown> | null;
  recommendations?: string[] | null;
  dominant_posture_type?: string | null;
  session_metrics?: Record<string, unknown> | null;
  analyzed_at: string;
}

export interface SessionReportDto {
  report_status: ReportStatus;
  voice_status: AnalysisComponentStatus;
  motion_status: AnalysisComponentStatus;
  session: BackendSessionDto;
  voice_analysis: VoiceAnalysisDto | null;
  motion_analysis: MotionAnalysisDto | null;
}
