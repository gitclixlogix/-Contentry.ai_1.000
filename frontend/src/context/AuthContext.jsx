'use client';

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { checkAuthStatus, logoutUser } from '../../src/lib/api';

const AuthContext = createContext(null);

// Pages that don't require authentication
const PUBLIC_PATHS = [
  '/contentry/auth/login',
  '/contentry/auth/signup',
  '/contentry/auth/forgot-password',
  '/contentry/auth/reset-password',
  '/contentry/auth/set-password',
  '/contentry/auth/sso-success',
  '/contentry/auth/verify-email',
  '/contentry/auth/accept-invite',
  '/contentry/terms',
  '/contentry/privacy',
];

// Check if a path is public
const isPublicPath = (pathname) => {
  return PUBLIC_PATHS.some(path => pathname?.startsWith(path));
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isHydrated, setIsHydrated] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  // UUID validation helper
  const isValidUUID = (str) => {
    if (!str) return false;
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    return uuidRegex.test(str);
  };

  // Handle hydration - only run on client
  useEffect(() => {
    setIsHydrated(true);
  }, []);

  // Load user from localStorage after hydration
  // Then verify with backend using HttpOnly cookie (ARCH-022)
  useEffect(() => {
    if (!isHydrated) return;

    const loadUser = async () => {
      try {
        // First, try to load cached user data from localStorage
        const savedUser = localStorage.getItem('contentry_user');
        if (savedUser) {
          const userData = JSON.parse(savedUser);
          
          // Validate that user ID is a proper UUID, not an email
          if (userData.id && !isValidUUID(userData.id) && userData.id.includes('@')) {
            console.warn('Invalid user ID format detected (email instead of UUID). Please re-login.');
            localStorage.removeItem('contentry_user');
            setUser(null);
            setIsLoading(false);
            return;
          }
          
          // Set cached user immediately for better UX
          setUser(userData);
        }

        // Verify authentication with backend using HttpOnly cookie (ARCH-022)
        // This ensures the cookie is still valid
        const authStatus = await checkAuthStatus();
        
        if (authStatus.authenticated && authStatus.user) {
          // Update with fresh user data from backend
          setUser(authStatus.user);
          localStorage.setItem('contentry_user', JSON.stringify(authStatus.user));
        } else if (!savedUser) {
          // No cached user and not authenticated via cookie
          setUser(null);
        }
        // If we have cached user but cookie verification failed,
        // we keep the cached user for offline/error scenarios
        // The API interceptor will handle 401s
        
      } catch (error) {
        console.error('Error during auth check:', error);
        // Keep cached user if available, otherwise clear
        const savedUser = localStorage.getItem('contentry_user');
        if (!savedUser) {
          setUser(null);
        }
      } finally {
        setIsLoading(false);
      }
    };

    loadUser();
  }, [isHydrated]);

  // Handle protected route redirects
  useEffect(() => {
    if (!isHydrated || isLoading) return;

    // If not on a contentry page, don't check auth
    if (!pathname?.startsWith('/contentry/')) return;

    // If on a public path, allow access
    if (isPublicPath(pathname)) return;

    // If no user and on protected route, redirect to login
    if (!user) {
      router.push('/contentry/auth/login');
    }
  }, [isHydrated, isLoading, user, pathname, router]);

  // Login function - called after successful login
  // Note: HttpOnly cookie is set by backend, we just store user data locally
  const login = useCallback((userData) => {
    try {
      // Store user data for UI purposes (non-sensitive)
      // JWT token is in HttpOnly cookie, not accessible here
      localStorage.setItem('contentry_user', JSON.stringify(userData));
      setUser(userData);
    } catch (error) {
      console.error('Error saving user to localStorage:', error);
    }
  }, []);

  // Logout function - calls backend to clear HttpOnly cookies (ARCH-022)
  const logout = useCallback(async () => {
    try {
      // Call backend to clear HttpOnly cookies
      await logoutUser();
      
      // Clear local state
      localStorage.removeItem('contentry_user');
      // Note: We no longer need to remove 'token' as it's in HttpOnly cookie
      setUser(null);
      router.push('/contentry/auth/login');
    } catch (error) {
      console.error('Error during logout:', error);
      // Even if API fails, clear local state
      localStorage.removeItem('contentry_user');
      setUser(null);
      router.push('/contentry/auth/login');
    }
  }, [router]);

  // Update user function
  const updateUser = useCallback((updates) => {
    if (!user) return;
    const updatedUser = { ...user, ...updates };
    try {
      localStorage.setItem('contentry_user', JSON.stringify(updatedUser));
      setUser(updatedUser);
    } catch (error) {
      console.error('Error updating user in localStorage:', error);
    }
  }, [user]);

  // Check if user has specific role
  const hasRole = useCallback((role) => {
    if (!user) return false;
    if (Array.isArray(role)) {
      return role.includes(user.role) || role.includes(user.enterprise_role);
    }
    return user.role === role || user.enterprise_role === role;
  }, [user]);

  // Check if user is enterprise admin
  const isEnterpriseAdmin = useCallback(() => {
    return user?.enterprise_role === 'enterprise_admin';
  }, [user]);

  // Check if user is manager
  const isManager = useCallback(() => {
    return user?.enterprise_role === 'manager';
  }, [user]);

  // Check if user is admin
  const isAdmin = useCallback(() => {
    return user?.role === 'admin';
  }, [user]);

  // Refresh authentication from backend (verifies HttpOnly cookie)
  const refreshAuth = useCallback(async () => {
    try {
      const authStatus = await checkAuthStatus();
      if (authStatus.authenticated && authStatus.user) {
        setUser(authStatus.user);
        localStorage.setItem('contentry_user', JSON.stringify(authStatus.user));
        return true;
      } else {
        setUser(null);
        localStorage.removeItem('contentry_user');
        return false;
      }
    } catch (error) {
      console.error('Error refreshing auth:', error);
      return false;
    }
  }, []);

  const value = {
    user,
    isLoading,
    isHydrated,
    isAuthenticated: !!user,
    login,
    logout,
    updateUser,
    hasRole,
    isEnterpriseAdmin,
    isManager,
    isAdmin,
    refreshAuth, // New: verify authentication with backend
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook to use auth context
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// HOC for protected pages
export function withAuth(Component, options = {}) {
  const { requiredRole, redirectTo = '/contentry/auth/login' } = options;

  return function ProtectedComponent(props) {
    const { user, isLoading, isHydrated, hasRole } = useAuth();
    const router = useRouter();

    useEffect(() => {
      if (!isHydrated || isLoading) return;

      if (!user) {
        router.push(redirectTo);
        return;
      }

      if (requiredRole && !hasRole(requiredRole)) {
        router.push('/contentry/dashboard');
      }
    }, [isHydrated, isLoading, user, hasRole, router]);

    // Show nothing while checking auth
    if (!isHydrated || isLoading) {
      return null;
    }

    // Show nothing if not authenticated
    if (!user) {
      return null;
    }

    // Show nothing if doesn't have required role
    if (requiredRole && !hasRole(requiredRole)) {
      return null;
    }

    return <Component {...props} />;
  };
}

export default AuthContext;
