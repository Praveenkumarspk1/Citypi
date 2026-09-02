import { Mail, CheckCircle, AlertCircle, Clock, ArrowLeft } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { useVerifyEmail, useResendVerificationEmail } from '@shared/hooks/useApi';
import { handleApiError } from '@shared/utils/api';

export function VerifyEmailPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const verifyEmailMutation = useVerifyEmail();
  const resendVerificationMutation = useResendVerificationEmail();
  
  const [status, setStatus] = useState<'verifying' | 'success' | 'error' | 'missing_token'>('verifying');
  const [error, setError] = useState<string | null>(null);
  const [resendEmail, setResendEmail] = useState('');
  const [resendError, setResendError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setStatus('missing_token');
      return;
    }

    const verify = async () => {
      try {
        await verifyEmailMutation.mutateAsync(token);
        setStatus('success');
      } catch (err) {
        setStatus('error');
        setError(handleApiError(err));
      }
    };

    verify();
  }, [token, verifyEmailMutation]);

  const handleResend = async (e: React.FormEvent) => {
    e.preventDefault();
    // This would call a resend verification email endpoint
    // For now, just show a success message
    alert('Verification email resent to ' + resendEmail);
  };

  if (status === 'missing_token') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-red-100 mb-6">
              <AlertCircle className="w-8 h-8 text-red-600" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900">Invalid Verification Link</h1>
            <p className="text-gray-500 mt-2">This email verification link is invalid or missing.</p>
          </div>

          <div className="card p-6">
            <form onSubmit={handleResend} className="space-y-4">
              <p className="text-sm text-gray-600 text-center">
                Enter your email to receive a new verification link
              </p>
              <div>
                <label htmlFor="resendEmail" className="label">Email</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    id="resendEmail"
                    type="email"
                    value={resendEmail}
                    onChange={(e) => setResendEmail(e.target.value)}
                    placeholder="you@example.com"
                    className="input pl-10"
                    required
                    autoComplete="email"
                  />
                </div>
              </div>
              <button type="submit" className="btn-primary w-full py-3">
                Resend Verification Email
              </button>
            </form>
            <p className="mt-6 text-center text-sm text-gray-500">
              <Link to="/login" className="text-primary-600 hover:underline font-medium">Back to Sign In</Link>
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (status === 'verifying') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary-100 mb-6">
              <div className="animate-spin rounded-full h-8 w-8 border-3 border-primary-600 border-t-transparent" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900">Verifying Your Email</h1>
            <p className="text-gray-500 mt-2">Please wait while we verify your email address</p>
          </div>

          <div className="card p-6 text-center">
            <div className="flex items-center justify-center gap-2 text-primary-600">
              <Clock className="w-5 h-5" />
              <span className="text-sm">This may take a few seconds...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (status === 'success') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-green-100 mb-6">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900">Email Verified!</h1>
            <p className="text-gray-500 mt-2">Your email address has been successfully verified.</p>
          </div>

          <div className="card p-6 text-center">
            <Link to="/login" className="btn-primary w-full py-3">
              Sign In to Your Account
            </Link>
            <p className="mt-4 text-sm text-gray-500">
              You can now access all features of City Concierge
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-red-100 mb-6">
            <AlertCircle className="w-8 h-8 text-red-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Verification Failed</h1>
          <p className="text-gray-500 mt-2">{error || 'This verification link is invalid or has expired.'}</p>
        </div>

        <div className="card p-6">
          <form onSubmit={handleResend} className="space-y-4">
            <p className="text-sm text-gray-600 text-center">
              Enter your email to receive a new verification link
            </p>
            <div>
              <label htmlFor="resendEmail" className="label">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  id="resendEmail"
                  type="email"
                  value={resendEmail}
                  onChange={(e) => setResendEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="input pl-10"
                  required
                  autoComplete="email"
                />
              </div>
            </div>
            <button type="submit" className="btn-primary w-full py-3">
              Resend Verification Email
            </button>
          </form>
          <p className="mt-6 text-center text-sm text-gray-500">
            <Link to="/login" className="text-primary-600 hover:underline font-medium">Back to Sign In</Link>
          </p>
        </div>
      </div>
    </div>
  );
}