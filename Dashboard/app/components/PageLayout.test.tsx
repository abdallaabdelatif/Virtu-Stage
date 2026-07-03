import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router';
import { AuthProvider } from '../context/AuthContext';
import { verifySessionCall } from '../services/authService';
import type { AuthUser } from '../types/auth';
import { clearAccessToken, getAccessToken } from '../utils/tokenStorage';
import { PageLayout } from './PageLayout';
import { ProtectedRoute } from './ProtectedRoute';

vi.mock('../services/authService', () => ({
  verifySessionCall: vi.fn(),
}));

vi.mock('../utils/tokenStorage', () => ({
  clearAccessToken: vi.fn(),
  getAccessToken: vi.fn(),
  setAccessToken: vi.fn(),
}));

const user: AuthUser = {
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

function LoginLocation() {
  const location = useLocation();
  return <div>{location.state === null ? 'Clean login' : 'Stale login'}</div>;
}

describe('PageLayout', () => {
  it('clears protected-route state during explicit logout', async () => {
    vi.mocked(getAccessToken).mockReturnValue('stored-token');
    vi.mocked(verifySessionCall).mockResolvedValue(user);

    render(
      <MemoryRouter initialEntries={['/library']}>
        <AuthProvider>
          <Routes>
            <Route path="/" element={<LoginLocation />} />
            <Route
              path="/library"
              element={
                <ProtectedRoute>
                  <PageLayout>
                    <div>Library page</div>
                  </PageLayout>
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </MemoryRouter>,
    );

    await screen.findByText('Library page');
    fireEvent.click(screen.getByRole('button', { name: 'Logout' }));

    expect(await screen.findByText('Clean login')).toBeInTheDocument();
    expect(clearAccessToken).toHaveBeenCalledOnce();
  });
});
