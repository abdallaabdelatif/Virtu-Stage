import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import * as allure from 'allure-js-commons';
import { MemoryRouter, Route, Routes } from 'react-router';
import { useAuth } from '../context/AuthContext';
import {
  forgotPasswordCall,
  loginCall,
  registerCall,
  resetPasswordCall,
} from '../services/authService';
import type { AuthUser } from '../types/auth';
import ForgotPassword from './forgot-password';
import Login from './home';
import Register from './register';
import ResetPassword from './reset-password';

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('../services/authService', () => ({
  forgotPasswordCall: vi.fn(),
  loginCall: vi.fn(),
  registerCall: vi.fn(),
  resetPasswordCall: vi.fn(),
}));

const mockedUseAuth = vi.mocked(useAuth);
const mockedLoginCall = vi.mocked(loginCall);
const mockedRegisterCall = vi.mocked(registerCall);
const mockedForgotPasswordCall = vi.mocked(forgotPasswordCall);
const mockedResetPasswordCall = vi.mocked(resetPasswordCall);

const authUser: AuthUser = {
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

function mockGuestAuth() {
  const login = vi.fn();
  mockedUseAuth.mockReturnValue({
    user: null,
    isAuthenticated: false,
    loading: false,
    login,
    logout: vi.fn(),
    updateUser: vi.fn(),
  });
  return { login };
}

function renderWithRoutes(
  element: React.ReactElement,
  path: string,
  initialEntry = path,
) {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path={path} element={element} />
        <Route path="/dashboard" element={<div>Dashboard Page</div>} />
        <Route path="/" element={<div>Login Route</div>} />
        <Route path="/forgot-password" element={<div>Forgot Route</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('auth pages', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGuestAuth();
  });

  it('blocks login submission when required fields are empty', async () => {
    await allure.feature('Auth Pages');
    await allure.story('Login form validation');

    renderWithRoutes(<Login />, '/');

    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    expect(mockedLoginCall).not.toHaveBeenCalled();
    expect(screen.getByLabelText(/email or username/i)).toBeRequired();
    expect(screen.getByLabelText(/^password$/i)).toBeRequired();
  });

  it('logs in and navigates to dashboard on success', async () => {
    await allure.feature('Auth Pages');
    await allure.story('Login success flow');

    const auth = mockGuestAuth();
    mockedLoginCall.mockResolvedValue({
      success: true,
      token: 'jwt-token',
      user: authUser,
    });
    renderWithRoutes(<Login />, '/');

    fireEvent.change(screen.getByLabelText(/email or username/i), {
      target: { value: 'sara@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), {
      target: { value: 'Strong1!' },
    });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() =>
      expect(mockedLoginCall).toHaveBeenCalledWith(
        'sara@example.com',
        'Strong1!',
      ),
    );
    expect(auth.login).toHaveBeenCalledWith(authUser, 'jwt-token');
    expect(await screen.findByText('Dashboard Page')).toBeInTheDocument();
  });

  it('rejects register submission when passwords do not match', async () => {
    await allure.feature('Auth Pages');
    await allure.story('Registration validation');

    renderWithRoutes(<Register />, '/register');

    fireEvent.change(screen.getByLabelText(/username/i), {
      target: { value: 'sara' },
    });
    fireEvent.change(screen.getByLabelText(/first name/i), {
      target: { value: 'Sara' },
    });
    fireEvent.change(screen.getByLabelText(/last name/i), {
      target: { value: 'Ahmed' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'female' }));
    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'sara@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), {
      target: { value: 'Strong1!' },
    });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: 'Different1!' },
    });
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    expect(screen.getByRole('alert')).toHaveTextContent(
      'Passwords do not match',
    );
    expect(mockedRegisterCall).not.toHaveBeenCalled();
  });

  it('registers and navigates to dashboard on success', async () => {
    await allure.feature('Auth Pages');
    await allure.story('Registration success flow');

    const auth = mockGuestAuth();
    mockedRegisterCall.mockResolvedValue({
      success: true,
      token: 'register-token',
      user: authUser,
    });
    renderWithRoutes(<Register />, '/register');

    fireEvent.change(screen.getByLabelText(/username/i), {
      target: { value: 'sara' },
    });
    fireEvent.change(screen.getByLabelText(/first name/i), {
      target: { value: 'Sara' },
    });
    fireEvent.change(screen.getByLabelText(/last name/i), {
      target: { value: 'Ahmed' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'female' }));
    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'SARA@Example.COM' },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), {
      target: { value: 'Strong1!' },
    });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: 'Strong1!' },
    });
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() =>
      expect(mockedRegisterCall).toHaveBeenCalledWith(
        'sara',
        'Sara',
        'Ahmed',
        'female',
        'sara@example.com',
        'Strong1!',
      ),
    );
    expect(auth.login).toHaveBeenCalledWith(authUser, 'register-token');
    expect(await screen.findByText('Dashboard Page')).toBeInTheDocument();
  });

  it('submits forgot-password email and shows success state', async () => {
    await allure.feature('Auth Pages');
    await allure.story('Forgot password flow');

    mockedForgotPasswordCall.mockResolvedValue({ message: 'sent' });
    renderWithRoutes(<ForgotPassword />, '/forgot-password');

    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'sara@example.com' },
    });
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }));

    await waitFor(() =>
      expect(mockedForgotPasswordCall).toHaveBeenCalledWith('sara@example.com'),
    );
    expect(await screen.findByText(/check your email/i)).toBeInTheDocument();
  });

  it('handles reset-password invalid token and success flow', async () => {
    await allure.feature('Auth Pages');
    await allure.story('Reset password flow');

    const invalidLinkView = renderWithRoutes(
      <ResetPassword />,
      '/reset-password',
    );
    expect(screen.getByText(/invalid reset link/i)).toBeInTheDocument();
    invalidLinkView.unmount();

    mockedResetPasswordCall.mockResolvedValue({ message: 'updated' });
    renderWithRoutes(
      <ResetPassword />,
      '/reset-password',
      '/reset-password?token=abc',
    );
    fireEvent.change(screen.getByLabelText(/^new password$/i), {
      target: { value: 'Strong1!' },
    });
    fireEvent.change(screen.getByLabelText(/confirm new password/i), {
      target: { value: 'Strong1!' },
    });
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }));

    await waitFor(() =>
      expect(mockedResetPasswordCall).toHaveBeenCalledWith('abc', 'Strong1!'),
    );
    expect(await screen.findByText(/password updated/i)).toBeInTheDocument();
  });
});
