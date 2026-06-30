import { beforeEach, describe, expect, it, vi } from 'vitest';
import * as allure from 'allure-js-commons';
import api from '../utils/api';
import { forgotPasswordCall, loginCall, registerCall } from './authService';
import { getDashboardStats } from './dashboardService';
import { getFileDownloadUrl, getFiles, uploadFile } from './libraryService';
import { getSessionById, getSessions } from './sessionService';

vi.mock('../utils/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockedApi = vi.mocked(api);

const userDto = {
  user_id: 'user-1',
  username: 'sara',
  email: 'sara@example.com',
  first_name: 'Sara',
  last_name: 'Ahmed',
  gender: 'female' as const,
  role: 'user' as const,
  is_active: true,
  avatar_url: null,
};

const sessionDto = {
  session_id: 'session-1',
  user_id: 'user-1',
  scenario_type: 'interview' as const,
  difficulty_level: 'medium' as const,
  status: 'completed' as const,
  start_time: '2026-06-30T10:00:00Z',
  end_time: '2026-06-30T10:08:30Z',
  overall_score: 84,
  voice_analysis_score: 80,
  motion_analysis_score: 88,
  created_at: '2026-06-30T09:59:00Z',
};

describe('frontend services', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('logs in with trimmed identity and maps the backend user', async () => {
    await allure.feature('Frontend Services');
    await allure.story('Authentication service');

    mockedApi.post.mockResolvedValueOnce({
      data: { access_token: 'jwt-token', token_type: 'bearer', user: userDto },
    });

    const result = await loginCall('  sara@example.com  ', 'Strong1!');

    expect(mockedApi.post).toHaveBeenCalledWith('/api/auth/login', {
      username_or_email: 'sara@example.com',
      password: 'Strong1!',
    });
    expect(result.token).toBe('jwt-token');
    expect(result.user.name).toBe('Sara Ahmed');
  });

  it('registers users using backend field names', async () => {
    await allure.feature('Frontend Services');
    await allure.story('Registration service');

    mockedApi.post.mockResolvedValueOnce({
      data: { access_token: 'register-token', user: userDto },
    });

    const result = await registerCall(
      'sara',
      'Sara',
      'Ahmed',
      'female',
      'sara@example.com',
      'Strong1!',
    );

    expect(mockedApi.post).toHaveBeenCalledWith('/api/auth/register', {
      username: 'sara',
      email: 'sara@example.com',
      password: 'Strong1!',
      first_name: 'Sara',
      last_name: 'Ahmed',
      gender: 'female',
    });
    expect(result.token).toBe('register-token');
  });

  it('normalizes forgot-password email before sending', async () => {
    await allure.feature('Frontend Services');
    await allure.story('Forgot password service');

    mockedApi.post.mockResolvedValueOnce({ data: { message: 'sent' } });

    await forgotPasswordCall('  SARA@Example.COM  ');

    expect(mockedApi.post).toHaveBeenCalledWith('/api/auth/forgot-password', {
      email: 'sara@example.com',
    });
  });

  it('maps session list and detail responses', async () => {
    await allure.feature('Frontend Services');
    await allure.story('Session service');

    mockedApi.get
      .mockResolvedValueOnce({ data: [sessionDto] })
      .mockResolvedValueOnce({ data: sessionDto });

    const list = await getSessions();
    const detail = await getSessionById('session-1');

    expect(mockedApi.get).toHaveBeenNthCalledWith(1, '/api/sessions/me');
    expect(mockedApi.get).toHaveBeenNthCalledWith(2, '/api/sessions/session-1');
    expect(list[0]).toMatchObject({
      id: 'session-1',
      scenario: 'Job Interview',
      status: 'Completed',
    });
    expect(detail.duration).toBe('8:30');
  });

  it('loads user and admin dashboard endpoints', async () => {
    await allure.feature('Frontend Services');
    await allure.story('Dashboard service');

    mockedApi.get
      .mockResolvedValueOnce({
        data: {
          total_sessions: 2,
          analyzed_sessions: 1,
          average_overall_score: 81,
          improvement_rate: null,
          score_history: [{ session_id: 's1', date: '2026-06-30', score: 81 }],
          analysis_history: [],
        },
      })
      .mockResolvedValueOnce({
        data: {
          total_users: 4,
          total_sessions: 10,
          platform_average_score: 77,
          sessions_today: 2,
          sessions_by_day: [{ date: '2026-06-30', count: 2 }],
          average_score_by_month: [{ month: '2026-06', score: 77 }],
          recent_registrations: [],
        },
      });

    const userDashboard = await getDashboardStats('user');
    const adminDashboard = await getDashboardStats('admin');

    expect(mockedApi.get).toHaveBeenNthCalledWith(1, '/api/dashboard/me');
    expect(mockedApi.get).toHaveBeenNthCalledWith(2, '/api/admin/dashboard');
    expect(userDashboard.totalSessions).toBe(2);
    expect(adminDashboard.totalUsers).toBe(4);
  });

  it('loads files, reports upload progress, and returns download URLs', async () => {
    await allure.feature('Frontend Services');
    await allure.story('Library service');

    const fileDto = {
      file_id: 'file-1',
      original_name: 'deck.pdf',
      content_type: 'application/pdf',
      size_bytes: 2048,
      upload_status: 'ready' as const,
      processing_status: 'queued' as const,
      slide_count: null,
      processing_error: null,
      created_at: '2026-06-30T10:00:00Z',
    };
    mockedApi.get
      .mockResolvedValueOnce({ data: [fileDto] })
      .mockResolvedValueOnce({ data: { url: 'https://signed.example/deck' } });
    mockedApi.post.mockImplementationOnce((_url, _body, config) => {
      config?.onUploadProgress?.({
        bytes: 50,
        lengthComputable: true,
        loaded: 50,
        total: 100,
      });
      return Promise.resolve({ data: fileDto });
    });

    const files = await getFiles();
    const onProgress = vi.fn();
    const uploaded = await uploadFile(
      new File(['pdf'], 'deck.pdf'),
      onProgress,
    );
    const downloadUrl = await getFileDownloadUrl('file-1');

    expect(mockedApi.get).toHaveBeenNthCalledWith(1, '/api/files');
    expect(mockedApi.post).toHaveBeenCalledWith(
      '/api/files',
      expect.any(FormData),
      expect.objectContaining({ timeout: 120_000 }),
    );
    expect(onProgress).toHaveBeenCalledWith(50);
    expect(files[0].name).toBe('deck.pdf');
    expect(uploaded.processingStatus).toBe('queued');
    expect(downloadUrl).toBe('https://signed.example/deck');
  });
});
