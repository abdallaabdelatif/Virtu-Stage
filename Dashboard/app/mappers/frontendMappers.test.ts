import { describe, expect, it } from 'vitest';
import * as allure from 'allure-js-commons';
import {
  mapAdminDashboard,
  mapAdminUser,
  mapUserDashboard,
} from './dashboardMapper';
import { mapLibraryFile } from './libraryMapper';
import {
  mapBackendSession,
  mapBackendSessionDetail,
  mapSessionStatus,
} from './sessionMapper';
import { mapBackendUser } from './userMapper';

describe('frontend mappers', () => {
  it('maps backend user DTOs into auth users', async () => {
    await allure.feature('Frontend Mappers');
    await allure.story('User mapper');

    const user = mapBackendUser({
      user_id: 'user-1',
      username: 'omar',
      email: 'omar@example.com',
      first_name: 'Omar',
      last_name: 'Ali',
      gender: null,
      role: 'admin',
      is_active: true,
      avatar_url: 'https://cdn.example/avatar.webp',
    });

    expect(user).toMatchObject({
      id: 'user-1',
      name: 'Omar Ali',
      role: 'admin',
      avatar: 'https://cdn.example/avatar.webp',
    });
  });

  it('maps session status, list items, and details', async () => {
    await allure.feature('Frontend Mappers');
    await allure.story('Session mapper');

    const session = {
      session_id: 'session-1',
      user_id: 'user-1',
      scenario_type: 'public_speaking' as const,
      difficulty_level: 'hard' as const,
      status: 'processing' as const,
      start_time: '2026-06-30T10:00:00Z',
      end_time: '2026-06-30T10:02:05Z',
      overall_score: null,
      created_at: '2026-06-30T09:59:00Z',
    };

    expect(mapSessionStatus('processing')).toBe('Processing Analysis');
    expect(mapBackendSession(session)).toMatchObject({
      id: 'session-1',
      scenario: 'Public Speaking',
      status: 'Processing Analysis',
      backendStatus: 'processing',
    });
    expect(mapBackendSessionDetail(session)).toMatchObject({
      title: 'Public Speaking Session',
      difficulty: 'hard',
      duration: '2:05',
    });
  });

  it('maps user and admin dashboard DTOs', async () => {
    await allure.feature('Frontend Mappers');
    await allure.story('Dashboard mapper');

    const userDashboard = mapUserDashboard({
      total_sessions: 3,
      analyzed_sessions: 2,
      average_overall_score: 82,
      improvement_rate: 12,
      score_history: [{ session_id: 's1', date: '2026-06-30', score: 82 }],
      analysis_history: [
        {
          session_id: 's1',
          label: 'Session 1',
          voice_score: 80,
          motion_score: 84,
        },
      ],
    });
    const adminDashboard = mapAdminDashboard({
      total_users: 5,
      total_sessions: 11,
      platform_average_score: 79,
      sessions_today: 2,
      sessions_by_day: [{ date: '2026-06-30', count: 2 }],
      average_score_by_month: [{ month: '2026-06', score: 79 }],
      recent_registrations: [
        {
          user_id: 'u1',
          name: 'Sara Ahmed',
          email: 'sara@example.com',
          created_at: '2026-06-30T10:00:00Z',
        },
      ],
    });

    expect(userDashboard.totalSessions).toBe(3);
    expect(userDashboard.voiceMotionData[0]).toEqual({
      label: 'Session 1',
      voice: 80,
      motion: 84,
    });
    expect(adminDashboard.totalUsers).toBe(5);
    expect(adminDashboard.adminScoreData[0]).toMatchObject({
      month: 'Jun',
      score: 79,
    });
  });

  it('maps admin users and library files for UI display', async () => {
    await allure.feature('Frontend Mappers');
    await allure.story('Admin and library mappers');

    const adminUser = mapAdminUser({
      user_id: 'u1',
      name: 'Regular User',
      email: 'user@example.com',
      role: 'user',
      is_active: false,
      session_count: 7,
      created_at: '2026-06-30T10:00:00Z',
    });
    const libraryFile = mapLibraryFile({
      file_id: 'file-1',
      original_name: 'training-deck.pptx',
      content_type:
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
      size_bytes: 2 * 1024 * 1024,
      upload_status: 'ready',
      processing_status: 'ready',
      slide_count: 12,
      processing_error: null,
      created_at: '2026-06-30T10:00:00Z',
    });

    expect(adminUser).toMatchObject({
      id: 'u1',
      sessions: 7,
      disabled: true,
    });
    expect(libraryFile).toMatchObject({
      id: 'file-1',
      type: 'PPTX',
      size: '2.00 MB',
      processingStatus: 'ready',
    });
  });
});
