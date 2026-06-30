import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router';
import {
  AlertTriangle,
  CheckCircle,
  CheckCircle2,
  Circle,
  KeyRound,
} from 'lucide-react';
import { Button } from '../components/Button';
import { EyeIcon } from '../components/icons';
import { Input } from '../components/Input';
import { resetPasswordCall } from '../services/authService';
import {
  getPasswordChecks,
  isStrongPassword,
} from '../utils/accountValidation';
import { getApiErrorMessage } from '../utils/apiError';

export default function ResetPassword() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token')?.trim() ?? '';
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState('');
  const passwordChecks = getPasswordChecks(password);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError('');

    if (!token) {
      setError('This password reset link is invalid.');
      return;
    }
    if (!isStrongPassword(password)) {
      setError('Password does not meet all strength requirements.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setIsSubmitting(true);
    try {
      await resetPasswordCall(token, password);
      setIsSuccess(true);
      setPassword('');
      setConfirmPassword('');
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
          'Unable to reset your password. The link may be invalid or expired.',
        ),
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#0a0c10] p-6 lg:p-12">
      <div className="pointer-events-none absolute left-0 top-0 h-[500px] w-full bg-gradient-to-b from-brand/10 to-transparent lg:from-brand/5" />
      <div className="pointer-events-none absolute right-[-5%] top-[-10%] h-[500px] w-[500px] rounded-full bg-brand/10 blur-[120px]" />
      <div className="pointer-events-none absolute bottom-[-10%] left-[-5%] h-[400px] w-[400px] rounded-full bg-[#0bda62]/5 blur-[100px]" />

      <div className="relative z-10 w-full max-w-md">
        <div className="relative overflow-hidden rounded-3xl border border-[#2a3325] bg-[#121610]/80 p-8 shadow-2xl backdrop-blur-xl lg:p-10">
          <div className="absolute left-0 top-0 h-1 w-full bg-gradient-to-r from-brand to-[#0bda62]" />

          {isSuccess ? (
            <div className="flex flex-col items-center py-6 text-center">
              <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-[#0bda62]/10">
                <CheckCircle className="h-8 w-8 text-[#0bda62]" />
              </div>
              <h1 className="mb-3 text-2xl font-bold text-white">
                Password updated
              </h1>
              <p className="mb-8 text-sm font-medium leading-relaxed text-[#d9d9d9]">
                Your password has been reset successfully. You can now sign in
                using your new password.
              </p>
              <Button
                fullWidth
                onClick={() => navigate('/', { replace: true })}
              >
                Continue to Login
              </Button>
            </div>
          ) : !token ? (
            <div className="flex flex-col items-center py-6 text-center">
              <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-red-500/10">
                <AlertTriangle className="h-8 w-8 text-red-400" />
              </div>
              <h1 className="mb-3 text-2xl font-bold text-white">
                Invalid reset link
              </h1>
              <p className="mb-8 text-sm font-medium leading-relaxed text-[#d9d9d9]">
                This link does not contain a password reset token. Request a new
                reset link and try again.
              </p>
              <Link
                to="/forgot-password"
                className="flex h-14 w-full items-center justify-center rounded-xl bg-brand px-6 font-bold text-brand-contrast shadow-xl shadow-brand/20 transition-all hover:brightness-110"
              >
                Request New Link
              </Link>
            </div>
          ) : (
            <>
              <div className="mb-8 mt-2 text-center">
                <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand/10">
                  <KeyRound className="h-7 w-7 text-brand-soft" />
                </div>
                <h1 className="mb-3 text-3xl font-black tracking-wide text-white">
                  Create New Password
                </h1>
                <p className="text-sm font-medium text-[#d9d9d9]">
                  Choose a strong password that you have not used before.
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-3">
                {error && (
                  <p
                    role="alert"
                    className="rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-center text-sm text-red-400"
                  >
                    {error}
                  </p>
                )}

                <Input
                  label="New Password"
                  type={showPassword ? 'text' : 'password'}
                  name="new-password"
                  autoComplete="new-password"
                  placeholder="Enter your new password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                  rightElement={
                    <button
                      type="button"
                      aria-label={
                        showPassword ? 'Hide password' : 'Show password'
                      }
                      onClick={() => setShowPassword((current) => !current)}
                    >
                      <EyeIcon open={showPassword} />
                    </button>
                  }
                />

                <div className="grid grid-cols-1 gap-x-3 gap-y-1 px-1 pb-2 sm:grid-cols-2">
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
                  label="Confirm New Password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  name="confirm-password"
                  autoComplete="new-password"
                  placeholder="Confirm your new password"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  required
                  rightElement={
                    <button
                      type="button"
                      aria-label={
                        showConfirmPassword
                          ? 'Hide password confirmation'
                          : 'Show password confirmation'
                      }
                      onClick={() =>
                        setShowConfirmPassword((current) => !current)
                      }
                    >
                      <EyeIcon open={showConfirmPassword} />
                    </button>
                  }
                />

                {confirmPassword && (
                  <p
                    className={`px-1 text-xs ${
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

                <div className="pt-3">
                  <Button fullWidth type="submit" loading={isSubmitting}>
                    Reset Password
                  </Button>
                </div>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function PasswordRequirement({ met, label }: { met: boolean; label: string }) {
  const Icon = met ? CheckCircle2 : Circle;

  return (
    <div
      className={`flex items-center gap-1.5 text-xs ${
        met ? 'text-[#0bda62]' : 'text-[#aeb4a8]'
      }`}
    >
      <Icon className="h-3.5 w-3.5 shrink-0" />
      <span>{label}</span>
    </div>
  );
}
