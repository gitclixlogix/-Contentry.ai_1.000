import { useState, useEffect, useCallback, useRef } from 'react';
import { getApiUrl } from '@/lib/api';

/**
 * Job Status Hook (ARCH-004)
 * 
 * Manages background job status with WebSocket real-time updates.
 * Used for async content analysis, content generation, image generation, etc.
 * 
 * Features:
 * - WebSocket connection for real-time updates
 * - Automatic reconnection on disconnect
 * - Fallback to polling if WebSocket unavailable
 * - Job cancellation support
 * - Progress tracking
 * 
 * Usage:
 *   const { status, progress, result, error, isLoading, isCompleted, cancel } = useJobStatus(jobId);
 */

// Job status constants
export const JOB_STATUS = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
  RETRYING: 'retrying',
};

// Helper function to get WebSocket URL from API URL
const getWebSocketUrl = (jobId, userId) => {
  const apiUrl = getApiUrl();
  // Convert HTTP(S) URL to WS(S) URL
  let wsBase = apiUrl.replace(/^http/, 'ws');
  // Remove /api/v1 or /api suffix if present for WebSocket (we'll add it back correctly)
  wsBase = wsBase.replace(/\/api\/v1$/, '').replace(/\/api$/, '');
  return `${wsBase}/api/v1/jobs/ws/${jobId}?user_id=${userId}`;
};

/**
 * Hook for tracking background job status
 * 
 * @param {string} jobId - The job ID to track
 * @param {Object} options - Optional configuration
 * @param {string} options.userId - User ID for authentication
 * @param {boolean} options.useWebSocket - Whether to use WebSocket (default: true)
 * @param {number} options.pollInterval - Polling interval in ms if not using WebSocket (default: 2000)
 * @param {function} options.onComplete - Callback when job completes
 * @param {function} options.onError - Callback when job fails
 * @param {function} options.onProgress - Callback on progress updates
 * 
 * @returns {Object} Job status object
 */
export default function useJobStatus(jobId, options = {}) {
  const {
    userId: providedUserId,
    useWebSocket = true,
    pollInterval = 2000,
    onComplete,
    onError,
    onProgress,
  } = options;

  // State
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  // Refs for cleanup
  const wsRef = useRef(null);
  const pollIntervalRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const isMountedRef = useRef(true);
  
  // Store callbacks in refs to avoid stale closure issues
  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);
  const onProgressRef = useRef(onProgress);
  
  // Update refs when callbacks change
  useEffect(() => {
    onCompleteRef.current = onComplete;
    onErrorRef.current = onError;
    onProgressRef.current = onProgress;
  }, [onComplete, onError, onProgress]);

  // Get user ID from localStorage if not provided
  const getUserId = useCallback(() => {
    if (providedUserId) return providedUserId;
    if (typeof window !== 'undefined') {
      const userStr = localStorage.getItem('contentry_user');
      if (userStr) {
        try {
          const user = JSON.parse(userStr);
          return user.id;
        } catch (e) {
          console.error('Failed to parse user data:', e);
        }
      }
    }
    return null;
  }, [providedUserId]);

  // Fetch job status via REST API
  const fetchJobStatus = useCallback(async () => {
    if (!jobId) return;
    
    const userId = getUserId();
    if (!userId) {
      setError('User not authenticated');
      return;
    }

    console.log('>>> POLLING JOB STATUS for jobId:', jobId);
    
    try {
      const API = getApiUrl();
      const response = await fetch(`${API}/jobs/${jobId}?user_id=${userId}`, {
        credentials: 'include',
        headers: {
          'X-User-ID': userId,  // Required for backend authentication
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (!isMountedRef.current) return;

      setStatus(data.status);
      setProgress(data.progress);
      
      if (data.status === JOB_STATUS.COMPLETED) {
        console.log('>>> JOB COMPLETED! Calling onComplete with result:', data.result?.overall_score);
        setResult(data.result);
        onCompleteRef.current?.(data.result);
        // Stop polling on completion
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
      } else if (data.status === JOB_STATUS.FAILED) {
        setError(data.error || 'Job failed');
        onErrorRef.current?.(data.error);
        // Stop polling on failure
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
      } else if (data.progress) {
        onProgressRef.current?.(data.progress);
      }
    } catch (err) {
      console.error('Failed to fetch job status:', err);
      if (isMountedRef.current) {
        setError(err.message);
      }
    }
  }, [jobId, getUserId, onComplete, onError, onProgress]);

  // Connect to WebSocket for real-time updates
  const connectWebSocket = useCallback(() => {
    if (!jobId || !useWebSocket) return;
    
    const userId = getUserId();
    if (!userId) {
      // Fall back to polling if no user ID
      return;
    }

    // Don't reconnect if already connected
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const wsUrl = getWebSocketUrl(jobId, userId);
      console.log('Connecting to WebSocket:', wsUrl);
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected for job:', jobId);
        if (isMountedRef.current) {
          setIsConnected(true);
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket message:', data);

          if (!isMountedRef.current) return;

          // Handle different message types
          if (data.type === 'connected' || data.type === 'status_update') {
            setStatus(data.status);
            if (data.progress) {
              setProgress(data.progress);
              onProgressRef.current?.(data.progress);
            }
            if (data.result) {
              setResult(data.result);
              onCompleteRef.current?.(data.result);
            }
            if (data.error) {
              setError(data.error);
              onErrorRef.current?.(data.error);
            }
          } else if (data.type === 'progress_update') {
            setProgress(data.progress);
            onProgressRef.current?.(data.progress);
          } else if (data.type === 'error') {
            setError(data.message || 'WebSocket error');
          } else if (data.type === 'ping') {
            // Respond to ping
            ws.send(JSON.stringify({ type: 'pong' }));
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        if (isMountedRef.current) {
          setIsConnected(false);
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        if (isMountedRef.current) {
          setIsConnected(false);
          
          // Reconnect after a delay if job is still processing
          if (status && status !== JOB_STATUS.COMPLETED && status !== JOB_STATUS.FAILED && status !== JOB_STATUS.CANCELLED) {
            reconnectTimeoutRef.current = setTimeout(() => {
              if (isMountedRef.current) {
                connectWebSocket();
              }
            }, 3000);
          }
        }
      };
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      // Fall back to polling
    }
  }, [jobId, useWebSocket, getUserId, status, onComplete, onError, onProgress]);

  // Start polling as fallback
  const startPolling = useCallback(() => {
    if (pollIntervalRef.current) return;
    
    // Initial fetch
    fetchJobStatus();
    
    // Set up polling interval
    pollIntervalRef.current = setInterval(fetchJobStatus, pollInterval);
  }, [fetchJobStatus, pollInterval]);

  // Cancel the job
  const cancel = useCallback(async () => {
    if (!jobId) return false;
    
    const userId = getUserId();
    if (!userId) {
      setError('User not authenticated');
      return false;
    }

    try {
      const API = getApiUrl();
      const response = await fetch(`${API}/jobs/${jobId}?user_id=${userId}`, {
        method: 'DELETE',
        credentials: 'include',
        headers: {
          'X-User-ID': userId,  // Required for backend authentication
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to cancel job: ${response.status}`);
      }

      const data = await response.json();
      if (isMountedRef.current) {
        setStatus(JOB_STATUS.CANCELLED);
        setError('Job cancelled by user');
      }
      return true;
    } catch (err) {
      console.error('Failed to cancel job:', err);
      if (isMountedRef.current) {
        setError(err.message);
      }
      return false;
    }
  }, [jobId, getUserId]);

  // Retry/restart the job (would need to create new job)
  const retry = useCallback(async () => {
    // This would need to be implemented with the original job parameters
    // For now, just reset state and let parent component re-submit
    setStatus(null);
    setProgress(null);
    setResult(null);
    setError(null);
  }, []);

  // Effect to initialize connection when jobId changes
  useEffect(() => {
    isMountedRef.current = true;

    if (!jobId) {
      // Reset state when no jobId
      setStatus(null);
      setProgress(null);
      setResult(null);
      setError(null);
      return;
    }

    // Initial fetch to get current status
    fetchJobStatus();

    // Try WebSocket first, fall back to polling
    if (useWebSocket) {
      connectWebSocket();
      
      // Also start polling as backup in case WebSocket fails
      // (will be disabled when WebSocket connects)
      setTimeout(() => {
        if (!isConnected && isMountedRef.current) {
          startPolling();
        }
      }, 2000);
    } else {
      startPolling();
    }

    // Cleanup
    return () => {
      isMountedRef.current = false;
      
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
      
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
  }, [jobId]); // Only re-run when jobId changes

  // Derived state
  const isLoading = status === JOB_STATUS.PENDING || status === JOB_STATUS.PROCESSING || status === JOB_STATUS.RETRYING;
  const isCompleted = status === JOB_STATUS.COMPLETED;
  const isFailed = status === JOB_STATUS.FAILED;
  const isCancelled = status === JOB_STATUS.CANCELLED;
  const progressPercentage = progress?.percentage || 0;
  const progressMessage = progress?.message || '';
  const currentStep = progress?.current_step || '';

  return {
    // Status
    status,
    progress,
    result,
    error,
    
    // Derived state
    isLoading,
    isCompleted,
    isFailed,
    isCancelled,
    isConnected,
    progressPercentage,
    progressMessage,
    currentStep,
    
    // Actions
    cancel,
    retry,
    refetch: fetchJobStatus,
  };
}

/**
 * Submit a job to the async endpoint and return the job ID
 * 
 * @param {string} endpoint - The async endpoint (e.g., '/content/analyze/async')
 * @param {Object} data - The request data
 * @param {string} userId - User ID
 * @returns {Promise<{jobId: string, error: string|null}>}
 */
export async function submitAsyncJob(endpoint, data, userId) {
  try {
    const API = getApiUrl();
    const response = await fetch(`${API}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': userId || '',  // Required for backend authentication
      },
      credentials: 'include',
      body: JSON.stringify({ ...data, user_id: userId }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    return { jobId: result.job_id, error: null };
  } catch (err) {
    console.error('Failed to submit async job:', err);
    return { jobId: null, error: err.message };
  }
}
