import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';

/**
 * Reusable hook for fetching admin analytics data
 * Consolidates all admin analytics API calls in one place
 */
export default function useAdminAnalytics(options = {}) {
  const {
    autoLoad = true,
    includeUserDemographics = false,
    includePostingPatterns = false,
    includeContentQuality = false,
    includeLanguageDistribution = false,
    includeUsersByCountry = false,
    includeCostMetrics = false,
  } = options;

  const [data, setData] = useState({
    demographics: null,
    postingPatterns: null,
    contentQuality: null,
    languages: null,
    geoData: null,
    geoCountryDetails: null,
    costMetrics: null,
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadAnalytics = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const requests = [];
      const keys = [];

      if (includeUserDemographics) {
        requests.push(api.get('/admin/analytics/user-demographics'));
        keys.push('demographics');
      }

      if (includePostingPatterns) {
        requests.push(api.get('/admin/analytics/posting-patterns'));
        keys.push('postingPatterns');
      }

      if (includeContentQuality) {
        requests.push(api.get('/admin/analytics/content-quality'));
        keys.push('contentQuality');
      }

      if (includeLanguageDistribution) {
        requests.push(api.get('/admin/analytics/language-distribution'));
        keys.push('languages');
      }

      if (includeUsersByCountry) {
        requests.push(api.get('/admin/analytics/users-by-country'));
        keys.push('geoData');
      }

      if (includeCostMetrics) {
        requests.push(api.get('/admin/analytics/cost-metrics'));
        keys.push('costMetrics');
      }

      const responses = await Promise.all(requests);
      
      const newData = {};
      responses.forEach((response, index) => {
        const key = keys[index];
        
        // Transform geo data to object format with country details
        if (key === 'geoData') {
          const geoDataObj = {};
          response.data.countries.forEach((country, idx) => {
            geoDataObj[country] = response.data.user_counts[idx];
          });
          newData.geoData = geoDataObj;
          newData.geoCountryDetails = response.data.country_details || {};
        } else {
          newData[key] = response.data;
        }
      });

      setData(prevData => ({ ...prevData, ...newData }));
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load analytics';
      setError(errorMessage);
      console.error('Analytics loading error:', err);
    } finally {
      setLoading(false);
    }
  }, [
    includeUserDemographics,
    includePostingPatterns,
    includeContentQuality,
    includeLanguageDistribution,
    includeUsersByCountry,
    includeCostMetrics,
  ]);

  useEffect(() => {
    if (autoLoad) {
      loadAnalytics();
    }
  }, [autoLoad, loadAnalytics]);

  return {
    data,
    loading,
    error,
    reload: loadAnalytics,
  };
}
