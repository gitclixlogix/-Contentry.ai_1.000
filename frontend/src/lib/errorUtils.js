/**
 * Utility functions for error handling across the application
 */

/**
 * Extract a human-readable error message from an API error response
 * Handles both string and object error details
 * 
 * @param {Error} error - The error object (usually from axios)
 * @param {string} fallbackMessage - Default message if extraction fails
 * @returns {string} Human-readable error message
 */
export function getErrorMessage(error, fallbackMessage = 'An unexpected error occurred') {
  const errorDetail = error?.response?.data?.detail;
  
  if (typeof errorDetail === 'object') {
    return errorDetail.message || errorDetail.error || JSON.stringify(errorDetail);
  }
  
  if (typeof errorDetail === 'string') {
    return errorDetail;
  }
  
  return error?.message || fallbackMessage;
}

/**
 * Check if error is a rate limit / quota exceeded error
 * 
 * @param {Error} error - The error object
 * @returns {boolean}
 */
export function isQuotaError(error) {
  const status = error?.response?.status;
  const detail = error?.response?.data?.detail;
  
  if (status === 429) return true;
  if (typeof detail === 'object' && detail.upgrade_url) return true;
  
  return false;
}

/**
 * Check if error is an authentication error
 * 
 * @param {Error} error - The error object
 * @returns {boolean}
 */
export function isAuthError(error) {
  const status = error?.response?.status;
  return status === 401 || status === 403;
}
