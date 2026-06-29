import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router';
import { useAuth } from '../context/AuthContext';
import { registerCall } from '../services/authService';
import { Input } from '../components/Input';
import { Button } from '../components/Button';
import { EyeIcon, VirtuStageLogo } from '../components/icons';
import type { Gender } from '../types/auth';
import { getApiErrorMessage } from '../utils/apiError';
import {
  getPasswordChecks,
  getUsernameError,
  isStrongPassword,
} from '../utils/accountValidation';
import { CheckCircle2, Circle } from 'lucide-react';

export default function Register() {
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated) navigate('/dashboard');
  }, [isAuthenticated, navigate]);

  const [username, setUsername] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [gender, setGender] = useState<Gender | ''>('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [usernameConflict, setUsernameConflict] = useState('');
  const [emailConflict, setEmailConflict] = useState('');
  const usernameValidationError = username ? getUsernameError(username) : null;
  const usernameError = usernameValidationError ?? usernameConflict;
  const passwordChecks = getPasswordChecks(password);

  const handleSubmit = async () => {
    if (
      !username ||
      !firstName ||
      !lastName ||
      !gender ||
      !email ||
      !password ||
      !confirmPassword
    ) {
      setError('Please fill in all fields');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    const invalidUsernameMessage = getUsernameError(username);
    if (invalidUsernameMessage) {
      setError(invalidUsernameMessage);
      return;
    }
    if (!isStrongPassword(password)) {
      setError('Password does not meet all strength requirements');
      return;
    }
    setLoading(true);
    setError('');
    setUsernameConflict('');
    setEmailConflict('');

    try {
      const result = await registerCall(
        username.trim(),
        firstName.trim(),
        lastName.trim(),
        gender,
        email.trim().toLowerCase(),
        password,
      );
      setLoading(false);
      login(result.user, result.token);
      navigate('/dashboard');
    } catch (err: unknown) {
      setLoading(false);
      const message = getApiErrorMessage(
        err,
        'An error occurred during registration',
      );
      const normalizedMessage = message.toLowerCase();

      if (normalizedMessage.includes('username')) {
        setUsernameConflict(message);
      } else if (normalizedMessage.includes('email')) {
        setEmailConflict(message);
      } else {
        setError(message);
      }
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
            Already have an account?
          </span>
          <Link
            to="/"
            className="min-w-[84px] flex items-center justify-center rounded-xl h-10 px-5 bg-[#5c7cff] text-white text-sm font-bold hover:bg-[#4a6aee] transition-all shadow-lg shadow-[#5c7cff]/20"
          >
            Sign In
          </Link>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-[480px]">
          <div className="bg-[#1b1d28]/60 border border-[#393f56] rounded-xl p-8 shadow-2xl backdrop-blur-md">
            <div className="text-center mb-8">
              <h1 className="text-white text-[32px] font-bold pb-2">
                Create Account
              </h1>
              <p className="text-[#9aa1bc]">
                Start your AI-enhanced VR training journey
              </p>
            </div>

            {error && (
              <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm text-center">
                {error}
              </div>
            )}

            <div className="space-y-1">
              <Input
                label="Username"
                placeholder="Choose a username"
                value={username}
                error={Boolean(usernameError)}
                onChange={(e) => {
                  setUsername(e.target.value);
                  setUsernameConflict('');
                  setError('');
                }}
              />
              <p
                className={`-mt-1 mb-2 text-xs ${
                  usernameError ? 'text-red-400' : 'text-[#5c6484]'
                }`}
              >
                {usernameError ??
                  '3–30 characters; letters, numbers, dots, and underscores only.'}
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <Input
                  label="First Name"
                  placeholder="First name"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                />
                <Input
                  label="Last Name"
                  placeholder="Last name"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                />
              </div>
              <Input
                label="Email Address"
                type="email"
                placeholder="Enter your email"
                value={email}
                error={Boolean(emailConflict)}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setEmailConflict('');
                  setError('');
                }}
              />
              {emailConflict && (
                <p className="-mt-1 mb-2 text-xs text-red-400">
                  {emailConflict}
                </p>
              )}
              <div className="mb-4">
                <label className="block text-[#9aa1bc] text-sm font-bold mb-2">
                  Gender
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {(['male', 'female'] as const).map((option) => (
                    <button
                      key={option}
                      type="button"
                      onClick={() => setGender(option)}
                      aria-pressed={gender === option}
                      className={`rounded-xl border px-4 py-3 text-sm font-bold capitalize transition-colors ${
                        gender === option
                          ? 'border-[#5c7cff] bg-[#5c7cff]/15 text-white'
                          : 'border-[#393f56] bg-[#1b1d28] text-[#9aa1bc] hover:border-[#5c7cff]/60 hover:text-white'
                      }`}
                    >
                      {option}
                    </button>
                  ))}
                </div>
              </div>
              <Input
                label="Password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Create a password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                rightElement={
                  <button
                    type="button"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    <EyeIcon open={showPassword} />
                  </button>
                }
              />
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-3 gap-y-1 px-1 pb-2">
                <PasswordRequirement
                  met={passwordChecks.minLength}
                  label="At least 8 characters"
                />
                <PasswordRequirement
                  met={passwordChecks.uppercase}
                  label="One uppercase letter"
                />
                <PasswordRequirement
                  met={passwordChecks.lowercase}
                  label="One lowercase letter"
                />
                <PasswordRequirement
                  met={passwordChecks.number}
                  label="One number"
                />
                <PasswordRequirement
                  met={passwordChecks.specialCharacter}
                  label="One special character"
                />
              </div>
              <Input
                label="Confirm Password"
                type={showConfirm ? 'text' : 'password'}
                placeholder="Confirm your password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
                rightElement={
                  <button
                    type="button"
                    aria-label={
                      showConfirm
                        ? 'Hide password confirmation'
                        : 'Show password confirmation'
                    }
                    onClick={() => setShowConfirm(!showConfirm)}
                  >
                    <EyeIcon open={showConfirm} />
                  </button>
                }
              />
              {confirmPassword && (
                <p
                  className={`-mt-1 mb-2 text-xs ${
                    password === confirmPassword
                      ? 'text-[#0bda62]'
                      : 'text-red-400'
                  }`}
                >
                  {password === confirmPassword
                    ? 'Passwords match'
                    : 'Passwords do not match'}
                </p>
              )}

              <div className="pt-2">
                <Button onClick={handleSubmit} loading={loading} fullWidth>
                  Create Account
                </Button>
              </div>
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

function PasswordRequirement({
  met,
  label,
}: {
  met: boolean;
  label: string;
}) {
  const Icon = met ? CheckCircle2 : Circle;

  return (
    <div
      className={`flex items-center gap-1.5 text-xs ${
        met ? 'text-[#0bda62]' : 'text-[#5c6484]'
      }`}
    >
      <Icon className="h-3.5 w-3.5 shrink-0" />
      <span>{label}</span>
    </div>
  );
}
