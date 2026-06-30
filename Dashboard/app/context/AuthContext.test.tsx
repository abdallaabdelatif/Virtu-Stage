import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import * as allure from 'allure-js-commons';
import { AuthProvider, useAuth } from './AuthContext';
import { verifySessionCall } from '../services/authService';
import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from '../utils/tokenStorage';
import type { AuthUser } from '../types/auth';

vi.mock('../services/authService', () => ({
  verifySessionCall: vi.fn(),
}));

vi.mock('../utils/tokenStorage', () => ({
  clearAccessToken: vi.fn(),
  getAccessToken: vi.fn(),
  setAccessToken: vi.fn(),
}));

const mockedVerifySessionCall = vi.mocked(verifySessionCall);
const mockedGetAccessToken = vi.mocked(getAccessToken);
const mockedSetAccessToken = vi.mocked(setAccessToken);
const mockedClearAccessToken = vi.mocked(clearAccessToken);

const testUser: AuthUser = {
  id: 'user-1',
  username: 'sara',
  firstName: 'Sara',
  lastName: 'Ahmed',
  name: 'Sara Ahmed',
  email: 'sara@example.com',
  role: 'user',
  isActive: true,
  avatar: null,
  gender: 'female',
};

function AuthHarness() {
  const { user, login, logout, updateUser, isAuthenticated } = useAuth();
  return (
    <div>
      <p>{isAuthenticated ? 'authenticated' : 'guest'}</p>
      <p>{user?.name ?? 'No user'}</p>
      <button type="button" onClick={() => login(testUser, 'new-token')}>
        Login
      </button>
      <button
        type="button"
        onClick={() =>
          updateUser({ firstName: 'Updated', name: 'Updated Ahmed' })
        }
      >
        Update User
      </button>
      <button type="button" onClick={logout}>
        Logout
      </button>
    </div>
  );
}

describe('AuthProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders children as guest when no token exists', async () => {
    await allure.feature('Auth Context');
    await allure.story('No stored session');

    mockedGetAccessToken.mockReturnValue(null);

    render(
      <AuthProvider>
        <AuthHarness />
      </AuthProvider>,
    );

    await screen.findByText('guest');
    expect(mockedVerifySessionCall).not.toHaveBeenCalled();
  });

  it('loads the current user when a token exists', async () => {
    await allure.feature('Auth Context');
    await allure.story('Current user loading');

    mockedGetAccessToken.mockReturnValue('stored-token');
    mockedVerifySessionCall.mockResolvedValue(testUser);

    render(
      <AuthProvider>
        <AuthHarness />
      </AuthProvider>,
    );

    expect(await screen.findByText('authenticated')).toBeInTheDocument();
    expect(screen.getByText('Sara Ahmed')).toBeInTheDocument();
  });

  it('logs in, updates user data, and logs out', async () => {
    await allure.feature('Auth Context');
    await allure.story('Login logout token storage');

    mockedGetAccessToken.mockReturnValue(null);

    render(
      <AuthProvider>
        <AuthHarness />
      </AuthProvider>,
    );

    await screen.findByText('guest');
    fireEvent.click(screen.getByRole('button', { name: 'Login' }));

    expect(mockedSetAccessToken).toHaveBeenCalledWith('new-token');
    expect(screen.getByText('authenticated')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Update User' }));
    expect(screen.getByText('Updated Ahmed')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Logout' }));
    await waitFor(() => expect(screen.getByText('guest')).toBeInTheDocument());
    expect(mockedClearAccessToken).toHaveBeenCalled();
  });

  it('clears the stored token when verification fails', async () => {
    await allure.feature('Auth Context');
    await allure.story('Failed session verification');

    mockedGetAccessToken.mockReturnValue('expired-token');
    mockedVerifySessionCall.mockRejectedValue(new Error('expired'));
    vi.spyOn(console, 'error').mockImplementation(() => undefined);

    render(
      <AuthProvider>
        <AuthHarness />
      </AuthProvider>,
    );

    await screen.findByText('guest');
    expect(mockedClearAccessToken).toHaveBeenCalled();
    vi.mocked(console.error).mockRestore();
  });
});
