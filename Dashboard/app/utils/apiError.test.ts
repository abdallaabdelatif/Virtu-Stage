import axios from 'axios';
import { describe, expect, it, vi } from 'vitest';
import * as allure from 'allure-js-commons';
import { getApiErrorMessage } from './apiError';
import { notifyUnauthorized, UNAUTHORIZED_EVENT } from './authEvents';

describe('API error handling', () => {
  it('extracts string and validation-list error details', async () => {
    await allure.feature('Frontend Error Handling');
    await allure.story('API error messages');

    expect(
      getApiErrorMessage(
        new axios.AxiosError('conflict', undefined, undefined, undefined, {
          status: 409,
          statusText: 'Conflict',
          headers: {},
          config: {} as never,
          data: { detail: 'Username is already taken' },
        }),
      ),
    ).toBe('Username is already taken');

    expect(
      getApiErrorMessage(
        new axios.AxiosError('validation', undefined, undefined, undefined, {
          status: 422,
          statusText: 'Unprocessable Entity',
          headers: {},
          config: {} as never,
          data: {
            detail: [{ msg: 'Invalid email' }, { msg: 'Weak password' }],
          },
        }),
      ),
    ).toBe('Invalid email, Weak password');
  });

  it('dispatches unauthorized events for auth cleanup listeners', async () => {
    await allure.feature('Frontend Error Handling');
    await allure.story('Unauthorized event');

    const listener = vi.fn();
    window.addEventListener(UNAUTHORIZED_EVENT, listener);

    notifyUnauthorized();

    expect(listener).toHaveBeenCalledOnce();
    window.removeEventListener(UNAUTHORIZED_EVENT, listener);
  });
});
