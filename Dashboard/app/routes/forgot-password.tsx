import { useState } from 'react';
import { useNavigate } from 'react-router';
import { ArrowLeft, CheckCircle, Mail } from 'lucide-react';
import { Input } from '../components/Input';
import { Button } from '../components/Button';
import { forgotPasswordCall } from '../services/authService';
import { getApiErrorMessage } from '../utils/apiError';

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError('');
    try {
      await forgotPasswordCall(email);
      setIsSuccess(true);
    } catch (requestError) {
      setError(
        getApiErrorMessage(requestError, 'Unable to send the reset link.'),
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0c10] flex items-center justify-center p-6 lg:p-12 relative overflow-hidden">
      {/* Background Ornaments (matches home.tsx) */}
      <div className="absolute top-0 left-0 w-full h-[500px] bg-gradient-to-b from-brand/10 lg:from-brand/5 to-transparent pointer-events-none" />
      <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] rounded-full bg-brand/10 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] left-[-5%] w-[400px] h-[400px] rounded-full bg-[#0bda62]/5 blur-[100px] pointer-events-none" />

      <div className="w-full max-w-md relative z-10">
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 text-[#d9d9d9] hover:text-white transition-colors mb-8 font-bold text-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Login
        </button>

        <div className="bg-[#121610]/80 backdrop-blur-xl border border-[#2a3325] rounded-3xl p-8 lg:p-10 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-brand to-[#0bda62]" />

          {isSuccess ? (
            <div className="flex flex-col items-center text-center py-6">
              <div className="w-16 h-16 rounded-2xl bg-[#0bda62]/10 flex items-center justify-center mb-6">
                <CheckCircle className="w-8 h-8 text-[#0bda62]" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-3">
                Check your email
              </h2>
              <p className="text-[#d9d9d9] mb-8 font-medium">
                If an account exists for <br />
                <span className="text-white font-bold">{email}</span>, you will
                receive a password reset link.
              </p>
              <Button fullWidth onClick={() => navigate('/')}>
                Return to Login
              </Button>
            </div>
          ) : (
            <>
              <div className="text-center mb-10 mt-2">
                <h2 className="text-3xl font-black text-white mb-3 tracking-wide">
                  Reset Password
                </h2>
                <p className="text-[#d9d9d9] font-medium text-sm">
                  Enter your email address and we'll send you a link to reset
                  your password.
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-5">
                {error && (
                  <p
                    role="alert"
                    className="rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-center text-sm text-red-400"
                  >
                    {error}
                  </p>
                )}
                <Input
                  label="Email Address"
                  type="email"
                  name="email"
                  autoComplete="email"
                  placeholder="name@company.com"
                  icon={Mail}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />

                <div className="pt-2">
                  <Button fullWidth type="submit" loading={isSubmitting}>
                    Send Reset Link
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
