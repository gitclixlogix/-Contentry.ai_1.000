import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw, Mail, AlertCircle } from 'lucide-react';
import { api } from '../lib/api';
import { ANALYSIS_DEBOUNCE_MS } from '../lib/config';
import type { User, StrategicProfile, AnalysisResult, EmailContent } from '../lib/types';
import { Header } from './Header';
import { LoginPrompt } from './LoginPrompt';
import { ProfileSelector } from './ProfileSelector';
import { ScoreGrid } from './ScoreCard';
import { RecommendationList } from './RecommendationList';
import { LoadingState, AnalyzingState, EmptyState } from './LoadingState';

interface AnalysisPanelProps {
  platform: 'gmail' | 'outlook';
  getEmailContent: () => Promise<EmailContent>;
  onContentChange?: (callback: () => void) => () => void;
}

export function AnalysisPanel({ platform, getEmailContent, onContentChange }: AnalysisPanelProps) {
  // Auth state
  const [user, setUser] = useState<User | null>(null);
  const [isAuthLoading, setIsAuthLoading] = useState(true);

  // Profile state
  const [profiles, setProfiles] = useState<StrategicProfile[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState<string | null>(null);
  const [isProfilesLoading, setIsProfilesLoading] = useState(false);

  // Content & Analysis state
  const [emailContent, setEmailContent] = useState<EmailContent>({ subject: '', body: '' });
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [lastAnalyzedContent, setLastAnalyzedContent] = useState<string>('');

  // Check authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const userData = await api.getUser();
        setUser(userData);
      } catch (error) {
        console.error('Auth check failed:', error);
      } finally {
        setIsAuthLoading(false);
      }
    };
    checkAuth();
  }, []);

  // Load profiles when authenticated
  useEffect(() => {
    if (!user) return;

    const loadProfiles = async () => {
      setIsProfilesLoading(true);
      try {
        const fetchedProfiles = await api.getStrategicProfiles();
        setProfiles(fetchedProfiles);

        const savedProfileId = await api.getSelectedProfile();
        if (savedProfileId && fetchedProfiles.some(p => p.id === savedProfileId)) {
          setSelectedProfileId(savedProfileId);
        } else if (fetchedProfiles.length > 0) {
          setSelectedProfileId(fetchedProfiles[0].id);
        }
      } catch (error) {
        console.error('Failed to load profiles:', error);
      } finally {
        setIsProfilesLoading(false);
      }
    };
    loadProfiles();
  }, [user]);

  // Fetch email content
  const fetchEmailContent = useCallback(async () => {
    try {
      const content = await getEmailContent();
      setEmailContent(content);
    } catch (error) {
      console.error('Failed to get email content:', error);
    }
  }, [getEmailContent]);

  // Listen for content changes
  useEffect(() => {
    fetchEmailContent();

    if (onContentChange) {
      return onContentChange(() => {
        fetchEmailContent();
      });
    }
  }, [fetchEmailContent, onContentChange]);

  // Combine subject and body for analysis
  const fullContent = `Subject: ${emailContent.subject}\n\n${emailContent.body}`.trim();

  // Debounced analysis
  useEffect(() => {
    if (!user || fullContent.length < 10) return;
    if (fullContent === lastAnalyzedContent) return;

    const timeoutId = setTimeout(() => {
      runAnalysis();
    }, ANALYSIS_DEBOUNCE_MS);

    return () => clearTimeout(timeoutId);
  }, [fullContent, user, selectedProfileId]);

  const runAnalysis = useCallback(async () => {
    if (fullContent.length < 10) {
      setAnalysisError('Please write more content to analyze');
      return;
    }

    setIsAnalyzing(true);
    setAnalysisError(null);

    try {
      const result = await api.analyzeContent(
        fullContent,
        selectedProfileId || undefined,
        platform,
        { email_subject: emailContent.subject }
      );
      if (result) {
        setAnalysisResult(result);
        setLastAnalyzedContent(fullContent);
      } else {
        setAnalysisError('Analysis failed. Please try again.');
      }
    } catch (error) {
      console.error('Analysis error:', error);
      setAnalysisError('Failed to analyze content.');
    } finally {
      setIsAnalyzing(false);
    }
  }, [fullContent, selectedProfileId, platform, emailContent.subject]);

  const handleProfileSelect = async (profileId: string) => {
    setSelectedProfileId(profileId);
    await api.setSelectedProfile(profileId);
    if (fullContent.length >= 10) {
      setLastAnalyzedContent('');
    }
  };

  const handleLogout = async () => {
    await api.clearAuth();
    setUser(null);
    setProfiles([]);
    setSelectedProfileId(null);
    setAnalysisResult(null);
  };

  const handleRefresh = () => {
    fetchEmailContent();
    setLastAnalyzedContent('');
    runAnalysis();
  };

  // Loading state
  if (isAuthLoading) {
    return (
      <div style={{ width: '100%', height: '100%', minHeight: '400px', backgroundColor: 'white' }}>
        <LoadingState message="Loading..." />
      </div>
    );
  }

  // Not authenticated
  if (!user) {
    return (
      <div style={{ width: '100%', height: '100%', minHeight: '400px', backgroundColor: 'white' }}>
        <LoginPrompt
          platform={platform}
          onLoginSuccess={() => {
            api.getUser().then(setUser);
          }}
        />
      </div>
    );
  }

  const violations = analysisResult?.violations || [];
  const recommendations = analysisResult?.recommendations || [];
  const scores = {
    compliance: analysisResult?.compliance_score || 0,
    cultural: analysisResult?.cultural_sensitivity_score || 0,
    accuracy: analysisResult?.accuracy_score || 0,
    overall: analysisResult?.overall_score || 0,
  };

  return (
    <div style={{ width: '100%', minHeight: '400px', backgroundColor: '#f9fafb', display: 'flex', flexDirection: 'column' }}>
      <Header user={user} onLogout={handleLogout} platform={platform} />

      <div style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Profile Selector */}
          <ProfileSelector
            profiles={profiles}
            selectedId={selectedProfileId}
            onSelect={handleProfileSelect}
            isLoading={isProfilesLoading}
          />

          {/* Email Preview */}
          <div style={{ backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb', padding: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '11px', fontWeight: '500', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Email Being Analyzed
              </span>
              <span style={{ fontSize: '11px', color: '#6b7280' }}>
                {fullContent.length} chars
              </span>
            </div>
            {emailContent.subject && (
              <div style={{ fontSize: '13px', fontWeight: '600', color: '#101828', marginBottom: '4px' }}>
                Subject: {emailContent.subject}
              </div>
            )}
            <div style={{
              fontSize: '13px',
              color: '#101828',
              backgroundColor: '#f9fafb',
              borderRadius: '4px',
              padding: '8px',
              maxHeight: '80px',
              overflowY: 'auto'
            }}>
              {emailContent.body ? (
                <p style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', margin: 0 }}>
                  {emailContent.body.slice(0, 300)}
                  {emailContent.body.length > 300 && '...'}
                </p>
              ) : (
                <p style={{ color: '#6b7280', fontStyle: 'italic', margin: 0 }}>
                  Start composing your email...
                </p>
              )}
            </div>
          </div>

          {/* Analyzing State */}
          {isAnalyzing && <AnalyzingState />}

          {/* Error State */}
          {analysisError && !isAnalyzing && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '12px',
              borderRadius: '8px',
              backgroundColor: '#fef2f2',
              border: '1px solid #fecaca',
              color: '#b91c1c',
              fontSize: '14px'
            }}>
              <AlertCircle style={{ width: '16px', height: '16px', flexShrink: 0 }} />
              <span>{analysisError}</span>
            </div>
          )}

          {/* Results */}
          {analysisResult && !isAnalyzing && (
            <>
              {/* Scores */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '11px', fontWeight: '500', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    3-Pillar Scores
                  </span>
                  <button
                    onClick={handleRefresh}
                    disabled={isAnalyzing}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      fontSize: '12px',
                      color: '#6941C6',
                      background: 'none',
                      border: 'none',
                      cursor: isAnalyzing ? 'not-allowed' : 'pointer',
                      opacity: isAnalyzing ? 0.5 : 1
                    }}
                  >
                    <RefreshCw style={{ width: '12px', height: '12px' }} />
                    Refresh
                  </button>
                </div>
                <ScoreGrid scores={scores} isLoading={isAnalyzing} />
              </div>

              {/* Recommendations */}
              <div>
                <span style={{ display: 'block', fontSize: '11px', fontWeight: '500', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>
                  Analysis & Recommendations
                </span>
                <div style={{ backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb', padding: '12px' }}>
                  <RecommendationList
                    violations={violations}
                    recommendations={recommendations}
                    isLoading={isAnalyzing}
                  />
                </div>
              </div>
            </>
          )}

          {/* Empty State */}
          {!fullContent && !analysisResult && (
            <EmptyState
              title="Ready to analyze"
              description="Start composing your email to get real-time content analysis"
            />
          )}
        </div>
      </div>

      {/* Footer */}
      <div style={{ padding: '12px', borderTop: '1px solid #f3f4f6', backgroundColor: 'white' }}>
        <p style={{ fontSize: '12px', textAlign: 'center', color: '#6b7280', margin: 0 }}>
          Powered by Contentry.ai
        </p>
      </div>
    </div>
  );
}
