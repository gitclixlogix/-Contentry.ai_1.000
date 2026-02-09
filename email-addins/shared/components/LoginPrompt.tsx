import React, { useState } from 'react';
import { LogIn, Shield, Sparkles, Zap, Loader2, AlertCircle, Eye, EyeOff } from 'lucide-react';
import { api } from '../lib/api';

interface LoginPromptProps {
  onLoginSuccess: () => void;
  platform?: 'gmail' | 'outlook';
}

export function LoginPrompt({ onLoginSuccess, platform }: LoginPromptProps) {
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

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      background: 'linear-gradient(to bottom, #F9F5FF, white)'
    }}>
      {/* Header */}
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <div style={{
          width: '64px',
          height: '64px',
          margin: '0 auto 16px',
          borderRadius: '16px',
          backgroundColor: '#6941C6',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 10px 25px -5px rgba(105, 65, 198, 0.25)'
        }}>
          <svg viewBox="0 0 24 24" style={{ width: '40px', height: '40px', color: 'white' }} fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
          </svg>
        </div>
        <h1 style={{ fontSize: '20px', fontWeight: '700', color: '#101828', margin: '0 0 8px' }}>Contentry.ai</h1>
        <p style={{ fontSize: '14px', color: '#6b7280', margin: 0 }}>
          Sign in to analyze your {platform === 'gmail' ? 'Gmail' : platform === 'outlook' ? 'Outlook' : 'email'} content
        </p>
      </div>

      {/* Login Form */}
      <div style={{ padding: '0 24px 16px' }}>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {error && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '12px',
              borderRadius: '8px',
              backgroundColor: '#fef2f2',
              border: '1px solid #fecaca',
              color: '#b91c1c',
              fontSize: '14px'
            }}>
              <AlertCircle style={{ width: '16px', height: '16px', flexShrink: 0 }} />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: '500', color: '#6b7280', marginBottom: '6px' }}>
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: '8px',
                border: '1px solid #e5e7eb',
                fontSize: '14px',
                outline: 'none',
                boxSizing: 'border-box'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: '500', color: '#6b7280', marginBottom: '6px' }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                style={{
                  width: '100%',
                  padding: '10px 40px 10px 12px',
                  borderRadius: '8px',
                  border: '1px solid #e5e7eb',
                  fontSize: '14px',
                  outline: 'none',
                  boxSizing: 'border-box'
                }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: 0
                }}
              >
                {showPassword ? (
                  <EyeOff style={{ width: '16px', height: '16px', color: '#9ca3af' }} />
                ) : (
                  <Eye style={{ width: '16px', height: '16px', color: '#9ca3af' }} />
                )}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading || !email || !password}
            style={{
              width: '100%',
              padding: '12px 16px',
              borderRadius: '12px',
              backgroundColor: isLoading || !email || !password ? '#d1d5db' : '#6941C6',
              border: 'none',
              color: 'white',
              fontWeight: '600',
              fontSize: '14px',
              cursor: isLoading || !email || !password ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px'
            }}
          >
            {isLoading ? (
              <><Loader2 style={{ width: '16px', height: '16px', animation: 'spin 1s linear infinite' }} /> Signing in...</>
            ) : (
              <><LogIn style={{ width: '16px', height: '16px' }} /> Sign In</>
            )}
          </button>
        </form>
      </div>

      {/* Features */}
      <div style={{ padding: '16px 24px', marginTop: 'auto' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#6b7280' }}>
            <Shield style={{ width: '12px', height: '12px', color: '#3b82f6' }} />
            <span>Compliance checking</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#6b7280' }}>
            <Sparkles style={{ width: '12px', height: '12px', color: '#a855f7' }} />
            <span>Real-time analysis</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#6b7280' }}>
            <Zap style={{ width: '12px', height: '12px', color: '#22c55e' }} />
            <span>Smart suggestions</span>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div style={{ padding: '16px', borderTop: '1px solid #f3f4f6' }}>
        <p style={{ fontSize: '12px', textAlign: 'center', color: '#6b7280', margin: 0 }}>
          Don't have an account?{' '}
          <a href="https://contentry.ai/contentry/auth" target="_blank" rel="noopener noreferrer" style={{ color: '#6941C6', textDecoration: 'none' }}>
            Sign up free
          </a>
        </p>
      </div>
    </div>
  );
}
