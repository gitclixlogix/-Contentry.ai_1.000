/**
 * Rate Limit Status Hook (ARCH-013)
 * 
 * Provides real-time rate limit status for the current user.
 * Shows remaining requests, costs, and warnings.
 */

import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';

export const useRateLimitStatus = (options = {}) => {
  const { 
    autoRefresh = true, 
    refreshInterval = 30000,  // 30 seconds
    operation = null  // Optional: check specific operation
  } = options;
  
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const fetchStatus = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get('/rate-limits/status');
      setStatus(response.data);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch rate limit status');
    } finally {
      setLoading(false);
    }
  }, []);
  
  const checkOperation = useCallback(async (op) => {
    try {
      const response = await api.get(`/rate-limits/check/${op}`);
      return response.data;
    } catch (err) {
      if (err.response?.status === 429) {
        return {
          allowed: false,
          ...err.response.data
        };
      }
      throw err;
    }
  }, []);
  
  // Initial fetch
  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);
  
  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(fetchStatus, refreshInterval);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchStatus]);
  
  // Computed values
  const isNearLimit = status?.hourly?.percentage_used > 80;
  const isAtLimit = status?.hourly?.remaining === 0;
  const tier = status?.tier || 'free';
  const tierName = status?.tier_name || 'Free';
  
  return {
    status,
    loading,
    error,
    refresh: fetchStatus,
    checkOperation,
    // Convenience getters
    tier,
    tierName,
    hourlyRemaining: status?.hourly?.remaining ?? -1,
    hourlyLimit: status?.hourly?.limit ?? -1,
    hourlyUsed: status?.hourly?.used ?? 0,
    hourlyResetSeconds: status?.hourly?.reset_seconds ?? 3600,
    dailyCost: status?.daily?.cost ?? 0,
    monthlyCost: status?.monthly?.cost ?? 0,
    isNearLimit,
    isAtLimit,
    warnings: status?.warnings || []
  };
};

export default useRateLimitStatus;
