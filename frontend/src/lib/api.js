import axios from 'axios';

export const getApiUrl = () => {
  // API Version (ARCH-014)
  const API_VERSION = 'v1';
  
  // In browser context
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    
    // For deployed environments (non-localhost), ALWAYS use relative /api/v1 path
    // This goes through Kubernetes ingress which routes to the backend
    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
      return `/api/${API_VERSION}`;
    }
    
    // For localhost development, use the env variable if set
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
    if (backendUrl) {
      return `${backendUrl}/api/${API_VERSION}`;
    }
    
    // Fallback for localhost
    return `http://localhost:8001/api/${API_VERSION}`;
  }
  
  // Server-side rendering: use env var or fall back to internal service URL
  const serverBackendUrl = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL;
  if (serverBackendUrl) {
    return `${serverBackendUrl}/api/${API_VERSION}`;
  }
  
  // Default fallback for local development
  return `http://localhost:8001/api/${API_VERSION}`;
};

/**
 * Create an Axios instance configured for HttpOnly cookie authentication (ARCH-022)
 * 
 * Security features:
 * - withCredentials: true - Automatically sends HttpOnly cookies with requests
 * - No manual Authorization header needed - cookies handle authentication
 * - X-User-ID header added for backend user context (non-sensitive)
 */
export const createAuthenticatedAxios = () => {
  const instance = axios.create({
    baseURL: getApiUrl(),
    withCredentials: true, // CRITICAL: Include HttpOnly cookies with all requests
  });

  // Add request interceptor for user context and correlation ID (ARCH-006)
  instance.interceptors.request.use(
    (config) => {
      if (typeof window !== 'undefined') {
        // Add user context
        const userStr = localStorage.getItem('contentry_user');
        if (userStr) {
          try {
            const user = JSON.parse(userStr);
            if (user.id) {
              // X-User-ID is for backend context, not authentication
              // Authentication is handled by HttpOnly cookies
              config.headers['X-User-ID'] = user.id;
            }
          } catch (e) {
            console.error('Failed to parse user data:', e);
          }
        }
        
        // Add correlation ID for distributed tracing (ARCH-006)
        // Generate a new correlation ID for each request if not already present
        if (!config.headers['X-Correlation-ID']) {
          config.headers['X-Correlation-ID'] = generateCorrelationId();
        }
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Add response interceptor to handle auth errors and capture correlation IDs
  instance.interceptors.response.use(
    (response) => {
      // Log correlation ID from response for debugging (ARCH-006)
      const correlationId = response.headers['x-correlation-id'];
      if (correlationId && process.env.NODE_ENV === 'development') {
        console.debug(`[API] Correlation ID: ${correlationId}`);
      }
      return response;
    },
    (error) => {
      // Log correlation ID on errors for debugging
      const correlationId = error.response?.headers?.['x-correlation-id'];
      if (correlationId) {
        console.error(`[API Error] Correlation ID: ${correlationId}`, error.message);
      }
      
      // If we get a 401, the cookie may have expired
      // The frontend should redirect to login
      if (error.response?.status === 401) {
        // Clear any cached user data
        if (typeof window !== 'undefined') {
          localStorage.removeItem('contentry_user');
          // Optionally redirect to login
          // window.location.href = '/contentry/auth/login';
        }
      }
      return Promise.reject(error);
    }
  );

  return instance;
};

/**
 * Generate a unique correlation ID for request tracing (ARCH-006)
 * Format: timestamp-randomhex (e.g., "1703847123456-a1b2c3d4")
 */
const generateCorrelationId = () => {
  const timestamp = Date.now();
  const random = Math.random().toString(16).substring(2, 10);
  return `${timestamp}-${random}`;
};

/**
 * API call helper with automatic cookie handling (ARCH-022)
 * 
 * Usage:
 *   const response = await apiCall('/auth/me');
 *   const response = await apiCall('/users/profile', { method: 'POST', data: {...} });
 */
export const apiCall = async (endpoint, options = {}) => {
  const api = createAuthenticatedAxios();
  const { method = 'GET', data, ...rest } = options;
  
  try {
    const response = await api.request({
      url: endpoint,
      method,
      data,
      ...rest,
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Check if user is currently authenticated by calling /auth/me
 * This verifies the HttpOnly cookie is valid
 */
export const checkAuthStatus = async () => {
  try {
    const api = createAuthenticatedAxios();
    const response = await api.get('/auth/me');
    return {
      authenticated: true,
      user: response.data.user,
    };
  } catch (error) {
    return {
      authenticated: false,
      user: null,
    };
  }
};

/**
 * Logout user by calling backend logout endpoint
 * This clears the HttpOnly cookies on the server side
 */
export const logoutUser = async () => {
  try {
    const api = createAuthenticatedAxios();
    await api.post('/auth/logout');
    // Clear local user data
    if (typeof window !== 'undefined') {
      localStorage.removeItem('contentry_user');
    }
    return { success: true };
  } catch (error) {
    // Even if the API call fails, clear local data
    if (typeof window !== 'undefined') {
      localStorage.removeItem('contentry_user');
    }
    return { success: false, error };
  }
};

/**
 * Default authenticated API instance (ARCH-022 Refactor)
 * 
 * This is the recommended way to make API calls in the application.
 * It automatically handles HttpOnly cookie authentication.
 * 
 * Usage:
 *   import api from '@/lib/api';
 *   
 *   // GET request
 *   const response = await api.get('/users/profile');
 *   
 *   // POST request
 *   const response = await api.post('/content/analyze', { content: '...' });
 *   
 *   // With headers
 *   const response = await api.get('/data', { headers: { 'X-Custom': 'value' } });
 */
const api = createAuthenticatedAxios();

/**
 * Get the correct avatar/image URL for display
 * Handles relative URLs from backend and ensures they work in both local dev and deployed environments
 * 
 * @param {string} url - The avatar URL (can be relative like /api/v1/uploads/avatars/... or absolute)
 * @returns {string|null} - The corrected URL for display
 */
export const getImageUrl = (url) => {
  if (!url) return null;
  // If it's a blob URL (temporary), return as-is
  if (url.startsWith('blob:')) return url;
  // If it's already a full URL, return as-is
  if (url.startsWith('http')) return url;
  // If it's a data URL, return as-is
  if (url.startsWith('data:')) return url;
  // For relative URLs starting with /api/, handle based on environment
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    // For deployed environments, use relative path (goes through ingress)
    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
      return url;
    }
  }
  // For localhost, prepend backend URL
  return `${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001'}${url}`;
};

export default api;
