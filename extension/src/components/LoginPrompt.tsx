import React, { useState } from 'react';
import { LogIn, Shield, Sparkles, Zap, Loader2, AlertCircle, Eye, EyeOff } from 'lucide-react';
import { api } from '~/lib/api';

interface LoginPromptProps {
  onLoginSuccess: () => void;
}

export function LoginPrompt({ onLoginSuccess }: LoginPromptProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const result = await api.login(email, password);
      if (result.success) {
        onLoginSuccess();
      } else {
        setError(result.error || 'Login failed');
      }
    } catch (err) {
      setError('Connection failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleWebLogin = () => {
    chrome.tabs.create({ url: api.getLoginUrl() });
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-brand-50 to-white">
      {/* Header */}
      <div className="p-6 text-center">
        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-brand-500 flex items-center justify-center shadow-lg shadow-brand-500/25">
          <svg 
            viewBox="0 0 24 24" 
            className="w-10 h-10 text-white"
            fill="currentColor"
          >
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
          </svg>
        </div>
        <h1 className="text-xl font-bold text-dark-text mb-2">Contentry.ai</h1>
        <p className="text-sm text-dark-tertiary">Sign in to analyze content</p>
      </div>

      {/* Login Form */}
      <div className="px-6 py-4">
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-dark-tertiary mb-1.5">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              className="w-full px-3 py-2.5 rounded-lg border border-gray-200 text-sm
                         focus:border-brand-500 focus:ring-2 focus:ring-brand-100 
                         transition-all outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-dark-tertiary mb-1.5">
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full px-3 py-2.5 pr-10 rounded-lg border border-gray-200 text-sm
                           focus:border-brand-500 focus:ring-2 focus:ring-brand-100 
                           transition-all outline-none"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading || !email || !password}
            className="w-full py-3 px-4 rounded-xl bg-brand-500 hover:bg-brand-600 
                       text-white font-semibold text-sm transition-all duration-200
                       flex items-center justify-center gap-2 shadow-lg shadow-brand-500/25
                       hover:shadow-xl hover:shadow-brand-500/30 hover:-translate-y-0.5
                       disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Signing in...
              </>
            ) : (
              <>
                <LogIn className="w-4 h-4" />
                Sign In
              </>
            )}
          </button>
        </form>

        <div className="mt-4 text-center">
          <button
            onClick={handleWebLogin}
            className="text-xs text-brand-500 hover:underline"
          >
            Or sign in with Google on web →
          </button>
        </div>
      </div>

      {/* Features */}
      <div className="px-6 py-4 mt-auto space-y-2">
        <div className="flex items-center gap-2 text-xs text-dark-tertiary">
          <Shield className="w-3 h-3 text-blue-500" />
          <span>Compliance checking</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-dark-tertiary">
          <Sparkles className="w-3 h-3 text-purple-500" />
          <span>Real-time analysis</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-dark-tertiary">
          <Zap className="w-3 h-3 text-green-500" />
          <span>Smart suggestions</span>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-100">
        <p className="text-xs text-center text-dark-tertiary">
          Don't have an account?{' '}
          <a 
            href="https://contentry.ai/contentry/auth" 
            target="_blank"
            rel="noopener noreferrer"
            className="text-brand-500 hover:underline"
          >
            Sign up free
          </a>
        </p>
      </div>
    </div>
  );
}
