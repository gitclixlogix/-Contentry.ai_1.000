// API Configuration
// In development, use the backend URL from environment
// In production, this will be the actual Contentry.ai API URL
export const API_BASE_URL = process.env.PLASMO_PUBLIC_API_URL || 'http://localhost:8001';

// Extension storage keys
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'contentry_auth_token',
  USER_DATA: 'contentry_user_data',
  SELECTED_PROFILE: 'contentry_selected_profile',
  SETTINGS: 'contentry_settings',
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
