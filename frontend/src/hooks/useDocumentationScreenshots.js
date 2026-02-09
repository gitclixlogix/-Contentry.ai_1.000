'use client';
import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';

/**
 * Hook to fetch and manage documentation screenshots
 */
export function useDocumentationScreenshots(guide) {
  const [screenshots, setScreenshots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchScreenshots = useCallback(async () => {
    try {
      setLoading(true);
      const endpoint = guide 
        ? `/documentation/screenshots/guide/${guide}`
        : '/documentation/screenshots';
      
      const response = await api.get(endpoint);
      setScreenshots(response.data.screenshots || []);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch screenshots:', err);
      setError(err.message || 'Failed to load screenshots');
    } finally {
      setLoading(false);
    }
  }, [guide]);

  const refreshAll = useCallback(async () => {
    try {
      setRefreshing(true);
      await api.post('/documentation/screenshots/refresh');
      // Wait a bit for refresh to start, then poll
      setTimeout(() => {
        fetchScreenshots();
        setRefreshing(false);
      }, 5000);
    } catch (err) {
      console.error('Failed to refresh screenshots:', err);
      setRefreshing(false);
    }
  }, [fetchScreenshots]);

  const refreshOne = useCallback(async (pageId) => {
    try {
      await api.post(`/documentation/screenshots/refresh/${pageId}`);
      // Wait and refetch
      setTimeout(() => fetchScreenshots(), 3000);
    } catch (err) {
      console.error(`Failed to refresh screenshot ${pageId}:`, err);
    }
  }, [fetchScreenshots]);

  useEffect(() => {
    fetchScreenshots();
  }, [fetchScreenshots]);

  return {
    screenshots,
    loading,
    error,
    refreshing,
    refreshAll,
    refreshOne,
    refetch: fetchScreenshots
  };
}

/**
 * Hook to fetch a single screenshot
 */
export function useScreenshot(pageId) {
  const [screenshot, setScreenshot] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchScreenshot = useCallback(async () => {
    if (!pageId) return;
    
    try {
      setLoading(true);
      const response = await api.get(
        `/documentation/screenshots/${pageId}`
      );
      setScreenshot(response.data);
      setError(null);
    } catch (err) {
      console.error(`Failed to fetch screenshot ${pageId}:`, err);
      setError(err.message || 'Failed to load screenshot');
    } finally {
      setLoading(false);
    }
  }, [pageId]);

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      await api.post(
        `/documentation/screenshots/refresh/${pageId}`
      );
      // Wait for capture and refetch
      setTimeout(() => fetchScreenshot(), 5000);
    } catch (err) {
      console.error(`Failed to refresh screenshot ${pageId}:`, err);
      setLoading(false);
    }
  }, [pageId, fetchScreenshot]);

  useEffect(() => {
    fetchScreenshot();
  }, [fetchScreenshot]);

  return {
    screenshot,
    loading,
    error,
    refresh,
    refetch: fetchScreenshot
  };
}

export default useDocumentationScreenshots;
