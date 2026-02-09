// API Configuration - will be overridden by environment
export const getApiBaseUrl = (): string => {
  // Check for environment-specific URL
  if (typeof window !== 'undefined') {
    // @ts-ignore
    return window.CONTENTRY_API_URL || 'http://localhost:8001';
  }
  return 'http://localhost:8001';
};

// Storage keys
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'contentry_auth_token',
  USER_DATA: 'contentry_user_data',
  SELECTED_PROFILE: 'contentry_selected_profile',
} as const;

// Analysis debounce delay (ms)
export const ANALYSIS_DEBOUNCE_MS = 1500;

// Brand colors
export const BRAND_COLORS = {
  primary: '#6941C6',
  secondary: '#7F56D9',
  lightTint: '#F9F5FF',
  darkText: '#101828',
} as const;
