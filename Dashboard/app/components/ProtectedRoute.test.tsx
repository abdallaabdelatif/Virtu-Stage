import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import * as allure from 'allure-js-commons';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router';
import { ProtectedRoute } from './ProtectedRoute';
import { useAuth } from '../context/AuthContext';
import type { AuthUser } from '../types/auth';

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

const mockedUseAuth = vi.mocked(useAuth);

const activeUser: AuthUser = {
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

function LoginPage() {
  const location = useLocation();
  const state = location.state as { from?: { pathname?: string } } | null;
  return (
    <div>
      <p>Login Page</p>
      <span>{state?.from?.pathname ?? 'No return path'}</span>
    </div>
  );
}

function renderProtected(initialPath = '/admin') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/dashboard" element={<div>Dashboard Page</div>} />
        <Route
          path="/admin"
          element={
            <ProtectedRoute allowedRoles={['admin']}>
              <div>Admin Content</div>
            </ProtectedRoute>
          }
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('redirects unauthenticated users to login', async () => {
    await allure.feature('Frontend Routing');
    await allure.story('Unauthenticated route protection');

    mockedUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isExplicitLogout: false,
      loading: false,
      login: vi.fn(),
      logout: vi.fn(),
      clearExplicitLogout: vi.fn(),
      updateUser: vi.fn(),
    });

    renderProtected();

    expect(screen.getByText('Login Page')).toBeInTheDocument();
    expect(screen.getByText('/admin')).toBeInTheDocument();
  });

  it('redirects inactive users to login', async () => {
    await allure.feature('Frontend Routing');
    await allure.story('Inactive account protection');

    mockedUseAuth.mockReturnValue({
      user: { ...activeUser, isActive: false },
      isAuthenticated: true,
      isExplicitLogout: false,
      loading: false,
      login: vi.fn(),
      logout: vi.fn(),
      clearExplicitLogout: vi.fn(),
      updateUser: vi.fn(),
    });

    renderProtected();

    expect(screen.getByText('Login Page')).toBeInTheDocument();
  });

  it('redirects users without the required role', async () => {
    await allure.feature('Frontend Routing');
    await allure.story('Role-based route protection');

    mockedUseAuth.mockReturnValue({
      user: activeUser,
      isAuthenticated: true,
      isExplicitLogout: false,
      loading: false,
      login: vi.fn(),
      logout: vi.fn(),
      clearExplicitLogout: vi.fn(),
      updateUser: vi.fn(),
    });

    renderProtected();

    expect(screen.getByText('Dashboard Page')).toBeInTheDocument();
  });

  it('renders children for authenticated users with allowed role', async () => {
    await allure.feature('Frontend Routing');
    await allure.story('Allowed route access');

    mockedUseAuth.mockReturnValue({
      user: { ...activeUser, role: 'admin' },
      isAuthenticated: true,
      isExplicitLogout: false,
      loading: false,
      login: vi.fn(),
      logout: vi.fn(),
      clearExplicitLogout: vi.fn(),
      updateUser: vi.fn(),
    });

    renderProtected();

    expect(screen.getByText('Admin Content')).toBeInTheDocument();
  });
});
