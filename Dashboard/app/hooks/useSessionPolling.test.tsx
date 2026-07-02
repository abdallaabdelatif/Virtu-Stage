import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import api from '../utils/api';
import { MAX_SESSION_POLLING_MS, useSessionPolling } from './useSessionPolling';

vi.mock('../utils/api', () => ({
  default: {
    get: vi.fn(),
  },
}));

const mockedGet = vi.mocked(api.get);

describe('useSessionPolling', () => {
  beforeEach(() => {
    mockedGet.mockReset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('stops when both analysis callbacks are ready', async () => {
    mockedGet.mockResolvedValue({
      data: {
        session_id: 'session-1',
        status: 'processing',
        voice_ready: true,
        motion_ready: true,
      },
    });

    const { result } = renderHook(() =>
      useSessionPolling('session-1', 'processing'),
    );

    await waitFor(() => expect(result.current.status).toBe('Completed'));
    expect(result.current.isPolling).toBe(false);
    expect(mockedGet).toHaveBeenCalledTimes(1);
  });

  it('stops after the polling safety deadline', async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-07-02T00:00:00Z'));
    mockedGet.mockResolvedValue({
      data: {
        session_id: 'session-2',
        status: 'processing',
        voice_ready: false,
        motion_ready: true,
      },
    });

    const { result } = renderHook(() =>
      useSessionPolling('session-2', 'processing'),
    );

    await act(async () => {
      await vi.advanceTimersByTimeAsync(MAX_SESSION_POLLING_MS + 3000);
    });

    expect(result.current.status).toBe('Failed');
    expect(result.current.isPolling).toBe(false);
  });
});
