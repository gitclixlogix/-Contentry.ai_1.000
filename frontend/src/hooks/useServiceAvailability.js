/**
 * Service Availability Hook (ARCH-003)
 * 
 * Provides real-time service availability status for graceful degradation.
 * Integrates with backend circuit breakers and feature flags.
 */

import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';

export const useServiceAvailability = (options = {}) => {
  const { 
    autoRefresh = true, 
    refreshInterval = 60000,  // 1 minute
  } = options;
  
  const [availability, setAvailability] = useState({});
  const [systemHealth, setSystemHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isDegraded, setIsDegraded] = useState(false);
  
  const fetchAvailability = useCallback(async () => {
    try {
      setLoading(true);
      const [availRes, healthRes] = await Promise.all([
        api.get('/api/system/availability'),
        api.get('/api/system/health')
      ]);
      
      setAvailability(availRes.data.availability || {});
      setIsDegraded(availRes.data.degraded || false);
      setSystemHealth(healthRes.data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch service availability:', err);
      setError(err.response?.data?.detail || 'Failed to check service status');
      // Don't block on availability check failure - assume services available
      setIsDegraded(false);
    } finally {
      setLoading(false);
    }
  }, []);
  
  // Initial fetch
  useEffect(() => {
    fetchAvailability();
  }, [fetchAvailability]);
  
  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(fetchAvailability, refreshInterval);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchAvailability]);
  
  // Check if a specific feature is available
  const isFeatureAvailable = useCallback((featureName) => {
    const featureStatus = availability[featureName];
    return featureStatus?.available !== false;
  }, [availability]);
  
  // Get unavailability reason
  const getUnavailabilityReason = useCallback((featureName) => {
    const featureStatus = availability[featureName];
    return featureStatus?.reason || null;
  }, [availability]);
  
  return {
    availability,
    systemHealth,
    loading,
    error,
    isDegraded,
    refresh: fetchAvailability,
    isFeatureAvailable,
    getUnavailabilityReason,
    // Convenience getters for common features
    isAIAvailable: isFeatureAvailable('ai_content_generation'),
    isImageGenAvailable: isFeatureAvailable('ai_image_generation'),
    isSocialPostingAvailable: isFeatureAvailable('social_posting'),
    isPaymentsAvailable: isFeatureAvailable('stripe_payments'),
  };
};

export default useServiceAvailability;
