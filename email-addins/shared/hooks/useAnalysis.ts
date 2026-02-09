import { useState, useCallback, useEffect, useRef } from 'react';
import { api } from '../lib/api';
import { ANALYSIS_DEBOUNCE_MS } from '../lib/config';
import type { AnalysisResult, EmailContent } from '../lib/types';

export function useAnalysis(
  profileId: string | null,
  platform: 'gmail' | 'outlook' = 'gmail'
) {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const lastContentRef = useRef<string>('');
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  const analyze = useCallback(async (content: EmailContent) => {
    const fullContent = `Subject: ${content.subject}\n\n${content.body}`.trim();
    
    if (fullContent.length < 10) {
      setError('Please write more content to analyze');
      return;
    }

    // Skip if content hasn't changed
    if (fullContent === lastContentRef.current) {
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      const analysisResult = await api.analyzeContent(
        fullContent,
        profileId || undefined,
        platform,
        { email_subject: content.subject }
      );
      
      if (analysisResult) {
        setResult(analysisResult);
        lastContentRef.current = fullContent;
      } else {
        setError('Analysis failed');
      }
    } catch (err) {
      console.error('Analysis error:', err);
      setError('Failed to analyze content');
    } finally {
      setIsAnalyzing(false);
    }
  }, [profileId, platform]);

  const analyzeDebounced = useCallback((content: EmailContent) => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      analyze(content);
    }, ANALYSIS_DEBOUNCE_MS);
  }, [analyze]);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
    lastContentRef.current = '';
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  return {
    result,
    isAnalyzing,
    error,
    analyze,
    analyzeDebounced,
    reset,
  };
}
