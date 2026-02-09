import { useState, useCallback } from 'react';
import api from '@/lib/api';
import { getErrorMessage } from '@/lib/errorUtils';
import { submitAsyncJob } from '@/hooks/useJobStatus';

/**
 * Reusable hook for content analysis (Updated with ARCH-004 async support)
 * Provides a consistent interface for analyzing content across the application
 * 
 * Features:
 * - Synchronous analysis (legacy, for quick operations)
 * - Asynchronous analysis (new, returns job_id for background processing)
 * 
 * Used by:
 * - AnalyzeContentTab
 * - ContentGenerationTab
 * - ScheduledPostsTab (for re-analysis)
 */
export default function useContentAnalyzer() {
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState(null);
  const [analysisStep, setAnalysisStep] = useState('');
  
  // Async job state (ARCH-004)
  const [jobId, setJobId] = useState(null);
  const [useAsyncMode, setUseAsyncMode] = useState(true); // Default to async

  /**
   * Clean summary text by removing markdown artifacts
   */
  const cleanSummaryText = (text) => {
    if (!text) return '';
    return text
      .replace(/\*\*/g, '')
      .replace(/\*/g, '')
      .replace(/_{2,}/g, '')
      .replace(/#/g, '')
      .replace(/`/g, '')
      .trim();
  };

  /**
   * Get user ID from localStorage
   */
  const getUserId = () => {
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
  };

  /**
   * Analyze content asynchronously (ARCH-004)
   * Returns job_id immediately, use useJobStatus hook to track progress
   * 
   * @param {string} content - The content to analyze
   * @param {Object} options - Optional parameters
   * @returns {Promise<{jobId: string, error: string|null}>}
   */
  const analyzeContentAsync = useCallback(async (content, options = {}) => {
    if (!content || !content.trim()) {
      setError('Content cannot be empty');
      return { jobId: null, error: 'Content cannot be empty' };
    }

    setAnalyzing(true);
    setError(null);
    setAnalysis(null);
    setJobId(null);
    setAnalysisStep('Submitting analysis job...');

    try {
      const userId = options.userId || getUserId();
      if (!userId) {
        throw new Error('User not authenticated');
      }

      const result = await submitAsyncJob('/content/analyze/async', {
        content: content.trim(),
        language: options.language || 'en',
        profile_id: options.profileId || null,
        platform_context: options.platformContext || null,
      }, userId);

      if (result.error) {
        throw new Error(result.error);
      }

      setJobId(result.jobId);
      setAnalysisStep('Analysis job submitted');
      
      return { jobId: result.jobId, error: null };
    } catch (err) {
      const errorMessage = getErrorMessage(err, 'Failed to submit analysis job');
      setError(errorMessage);
      console.error('Content analysis submission error:', err);
      return { jobId: null, error: errorMessage };
    } finally {
      setAnalyzing(false);
    }
  }, []);

  /**
   * Handle async job completion - set analysis result
   */
  const handleJobComplete = useCallback((result) => {
    // Clean the summary text
    const cleanedAnalysis = {
      ...result,
      summary: cleanSummaryText(result?.summary)
    };
    setAnalysis(cleanedAnalysis);
    setJobId(null);
  }, []);

  /**
   * Handle async job error
   */
  const handleJobError = useCallback((error) => {
    setError(error);
    setJobId(null);
  }, []);

  /**
   * Analyze content using the backend API (synchronous - legacy)
   * @param {string} content - The content to analyze
   * @param {Object} options - Optional parameters
   * @param {string} options.tone - Writing tone
   * @param {string} options.jobTitle - User's job title
   * @param {string} options.language - Content language
   * @param {string} options.userId - User ID for tracking
   * @param {boolean} options.showProgress - Show progress steps (default: false)
   * @param {boolean} options.async - Use async mode (default: true)
   * @returns {Promise<Object>} Analysis result
   */
  const analyzeContent = useCallback(async (content, options = {}) => {
    // Use async mode by default unless explicitly disabled
    if (options.async !== false && useAsyncMode) {
      return analyzeContentAsync(content, options);
    }

    // Legacy synchronous mode
    if (!content || !content.trim()) {
      setError('Content cannot be empty');
      return null;
    }

    setAnalyzing(true);
    setError(null);
    setAnalysis(null);

    try {
      // Get user_id from localStorage if not provided in options
      let userId = options.userId;
      if (!userId && typeof window !== 'undefined') {
        const userStr = localStorage.getItem('contentry_user');
        if (userStr) {
          const user = JSON.parse(userStr);
          userId = user.id;
        }
      }

      if (!userId) {
        throw new Error('User not authenticated');
      }

      // Show progress steps if requested
      if (options.showProgress) {
        setAnalysisStep('Initializing analysis...');
        await new Promise(resolve => setTimeout(resolve, 300));
        
        setAnalysisStep('Checking policy compliance...');
        await new Promise(resolve => setTimeout(resolve, 300));
        
        setAnalysisStep('Analyzing cultural sensitivity...');
        await new Promise(resolve => setTimeout(resolve, 300));
        
        setAnalysisStep('Generating recommendations...');
      }

      const response = await api.post('/content/analyze', {
        content: content.trim(),
        tone: options.tone || 'professional',
        job_title: options.jobTitle || '',
        language: options.language || 'en',
        user_id: userId,
        profile_id: options.profileId || null,  // Strategic Profile ID for profile-aware analysis
      });

      // Clean the summary text
      const cleanedAnalysis = {
        ...response.data,
        summary: cleanSummaryText(response.data.summary)
      };

      setAnalysis(cleanedAnalysis);
      return cleanedAnalysis;
    } catch (err) {
      const errorMessage = getErrorMessage(err, 'Failed to analyze content');
      setError(errorMessage);
      console.error('Content analysis error:', err);
      return null;
    } finally {
      setAnalyzing(false);
      setAnalysisStep('');
    }
  }, [useAsyncMode, analyzeContentAsync]);

  /**
   * Generate content asynchronously (ARCH-004)
   * Returns job_id immediately, use useJobStatus hook to track progress
   */
  const generateContentAsync = useCallback(async (prompt, options = {}) => {
    if (!prompt || !prompt.trim()) {
      setError('Prompt cannot be empty');
      return { jobId: null, error: 'Prompt cannot be empty' };
    }

    setAnalyzing(true);
    setError(null);
    setJobId(null);

    try {
      const userId = options.userId || getUserId();
      if (!userId) {
        throw new Error('User not authenticated');
      }

      const result = await submitAsyncJob('/content/generate/async', {
        prompt: prompt.trim(),
        language: options.language || 'en',
        profile_id: options.profileId || null,
        platforms: options.platforms || [],
        tone: options.tone || 'professional',
        content_type: options.contentType || 'post',
      }, userId);

      if (result.error) {
        throw new Error(result.error);
      }

      setJobId(result.jobId);
      return { jobId: result.jobId, error: null };
    } catch (err) {
      const errorMessage = getErrorMessage(err, 'Failed to submit generation job');
      setError(errorMessage);
      return { jobId: null, error: errorMessage };
    } finally {
      setAnalyzing(false);
    }
  }, []);

  /**
   * Rewrite content using the backend API
   * @param {string} content - The content to rewrite
   * @param {Object} options - Optional parameters
   * @returns {Promise<Object>} Rewrite result with rewritten_content
   */
  const rewriteContent = useCallback(async (content, options = {}) => {
    if (!content || !content.trim()) {
      setError('Content cannot be empty');
      return null;
    }

    setAnalyzing(true);
    setError(null);

    try {
      let userId = options.userId;
      if (!userId && typeof window !== 'undefined') {
        const userStr = localStorage.getItem('contentry_user');
        if (userStr) {
          const user = JSON.parse(userStr);
          userId = user.id;
        }
      }

      if (!userId) {
        throw new Error('User not authenticated');
      }

      const response = await api.post('/content/rewrite', {
        content: content.trim(),
        tone: options.tone || 'professional',
        job_title: options.jobTitle || '',
        language: options.language || 'en',
        user_id: userId,
        hashtag_count: options.hashtagCount || 3,
        profile_id: options.profileId || null,  // Strategic Profile ID for profile-aware rewrite
      });

      return response.data;
    } catch (err) {
      const errorMessage = getErrorMessage(err, 'Failed to rewrite content');
      setError(errorMessage);
      console.error('Content rewrite error:', err);
      return null;
    } finally {
      setAnalyzing(false);
    }
  }, []);

  /**
   * Reset the analysis state
   */
  const resetAnalysis = useCallback(() => {
    setAnalysis(null);
    setError(null);
    setAnalyzing(false);
    setAnalysisStep('');
    setJobId(null);
  }, []);

  /**
   * Set analysis directly (for loading from history, etc.)
   */
  const setAnalysisResult = useCallback((result) => {
    setAnalysis(result);
    setError(null);
  }, []);

  /**
   * Toggle async mode
   */
  const toggleAsyncMode = useCallback((enabled) => {
    setUseAsyncMode(enabled);
  }, []);

  return {
    // State
    analyzing,
    analysis,
    error,
    analysisStep,
    jobId,          // ARCH-004: Current async job ID
    useAsyncMode,   // ARCH-004: Whether async mode is enabled
    
    // Actions
    analyzeContent,
    analyzeContentAsync,    // ARCH-004: Async analysis
    generateContentAsync,   // ARCH-004: Async generation
    rewriteContent,
    resetAnalysis,
    setAnalysisResult,
    toggleAsyncMode,        // ARCH-004: Toggle async mode
    
    // Async job handlers
    handleJobComplete,      // ARCH-004: Handle job completion
    handleJobError,         // ARCH-004: Handle job error
  };
}
