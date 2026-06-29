import { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router';
import { useAuth } from '../context/AuthContext';
import { loginCall } from '../services/authService';
import { Input } from '../components/Input';
import { Button } from '../components/Button';
import { EyeIcon, VirtuStageLogo } from '../components/icons';
import type { UserRole } from '../types/auth';
import { getApiErrorMessage } from '../utils/apiError';

interface LoginLocationState {
  from?: {
    pathname?: string;
  };
}

const getRedirectTarget = (role: UserRole, path: string): string => {
  const userOnlyRoutes = ['/sessions', '/analytics', '/library', '/session'];
  const isUserOnly = userOnlyRoutes.some(
    (route) => path === route || path.startsWith(route + '/'),
  );

  if (role === 'admin' && isUserOnly) {
    return '/dashboard';
  }
  if (role === 'user' && path === '/admin') {
    return '/dashboard';
  }
  return path;
};

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated, user } = useAuth();

  const locationState = location.state as LoginLocationState | null;
  const from = locationState?.from?.pathname || '/dashboard';

  useEffect(() => {
    if (isAuthenticated && user) {
      navigate(getRedirectTarget(user.role, from), { replace: true });
    }
  }, [isAuthenticated, user, navigate, from]);

  const [usernameOrEmail, setUsernameOrEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    if (!usernameOrEmail || !password) {
      setError('Please fill in all fields');
      return;
    }
    setLoading(true);
    setError('');

    try {
      const result = await loginCall(usernameOrEmail, password);
      setLoading(false);
      login(result.user, result.token);
      navigate(getRedirectTarget(result.user.role, from), { replace: true });
    } catch (err: unknown) {
      setLoading(false);
      setError(getApiErrorMessage(err, 'An error occurred during login'));
    }
  };

  return (
    <div
      className="relative min-h-screen flex flex-col text-white"
      style={{
        backgroundColor: '#0f1323',
        backgroundImage:
          'radial-gradient(at 0% 0%, hsla(228,100%,15%,1) 0, transparent 50%), radial-gradient(at 100% 100%, hsla(230,100%,20%,1) 0, transparent 50%)',
      }}
    >
      {/* Header */}
      <header className="flex items-center justify-between px-6 md:px-10 py-4 border-b border-[#272b3a] bg-[#0f1323]/30 backdrop-blur-sm sticky top-0 z-50">
        <div className="flex items-center gap-3 text-[#5c7cff]">
          <VirtuStageLogo className="w-6 h-6" />
          <h2 className="text-white text-xl font-bold">VirtuStage</h2>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-gray-400 text-sm hidden md:block">
            New to VirtuStage?
          </span>
          <Link
            to="/register"
            className="min-w-[84px] flex items-center justify-center rounded-xl h-10 px-5 bg-[#5c7cff] text-white text-sm font-bold hover:bg-[#4a6aee] transition-all shadow-lg shadow-[#5c7cff]/20"
          >
            Sign Up
          </Link>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-[480px]">
          <div className="bg-[#1b1d28]/60 border border-[#393f56] rounded-xl p-8 shadow-2xl backdrop-blur-md">
            {/* Title */}
            <div className="text-center mb-8">
              <h1 className="text-white text-[32px] font-bold pb-2">
                Welcome Back
              </h1>
              <p className="text-[#9aa1bc]">
                Log in to continue your AI-enhanced VR training
              </p>
            </div>

            {/* Error */}
            {error && (
              <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm text-center">
                {error}
              </div>
            )}

            {/* Form */}
            <div className="space-y-1">
              <Input
                label="Email or Username"
                type="text"
                placeholder="Enter your email or username"
                value={usernameOrEmail}
                onChange={(e) => setUsernameOrEmail(e.target.value)}
              />

              <Input
                label="Password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
                rightElement={
                  <button onClick={() => setShowPassword(!showPassword)}>
                    <EyeIcon open={showPassword} />
                  </button>
                }
              />

              <div className="flex justify-end text-sm font-bold mb-6">
                <button
                  type="button"
                  onClick={() => navigate('/forgot-password')}
                  className="text-[#5c7cff] hover:text-[#7691ff] hover:underline underline-offset-4 transition-all"
                >
                  Forgot Password?
                </button>
              </div>

              <Button onClick={handleSubmit} loading={loading} fullWidth>
                Sign In
              </Button>
            </div>

          </div>
        </div>
      </main>

      <footer className="p-6 text-center text-[#5c6484] text-xs">
        © 2026 VirtuStage AI Training Systems. All rights reserved.
      </footer>
    </div>
  );
}
