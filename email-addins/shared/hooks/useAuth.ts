import { useState, useEffect, useCallback } from 'react';
import { api } from '../lib/api';
import type { User } from '../lib/types';

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const userData = await api.getUser();
        setUser(userData);
      } catch (err) {
        console.error('Auth check failed:', err);
        setError('Failed to check authentication');
      } finally {
        setIsLoading(false);
      }
    };
    checkAuth();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await api.login(email, password);
      if (result.success && result.user) {
        setUser(result.user);
        return { success: true };
      }
      setError(result.error || 'Login failed');
      return { success: false, error: result.error };
    } catch (err) {
      const errorMsg = 'Connection failed';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    await api.clearAuth();
    setUser(null);
  }, []);

  return { user, isLoading, error, login, logout, isAuthenticated: !!user };
}
